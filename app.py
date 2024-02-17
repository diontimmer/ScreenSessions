from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
import subprocess
import threading
import tailer
import os
import re
import json
import time

app = Flask(__name__)
socketio = SocketIO(app)
session_output_tasks = {}
LOG_ROOT = "/tmp/screen/logs"

if not os.path.exists(LOG_ROOT):
    os.makedirs(LOG_ROOT)


def load_whitelist():
    try:
        with open("config.json", "r") as f:
            cmd_whitelist = json.load(f)["cmd_whitelist"]
    except Exception as e:
        print(f"Error loading whitelist: {e}")
        cmd_whitelist = []
    return cmd_whitelist


def get_screen_sessions():
    try:
        output = subprocess.check_output("screen -ls", shell=True).decode("utf-8")
        lines = output.split("\n")
        sessions = [line.split()[0] for line in lines if re.search(r"\d+\.", line)]
        return sessions
    except subprocess.CalledProcessError as e:
        print(f"Error getting screen sessions: {e}")
        return []


def check_session_loggers():
    sessions = get_screen_sessions()
    for session in sessions:
        log_file_path = os.path.join(LOG_ROOT, f"{session}.log")
        if not os.path.exists(log_file_path):
            print(f"Enabling logging for {session}")
            enable_logging(session)
            time.sleep(0.5)


def enable_logging(session):
    if "." in session:
        session_id = session.split(".")[0]
    log_file_path = os.path.join(LOG_ROOT, f"{session}.log")
    cmd = f"screen -S {session_id} -X logfile {log_file_path}"
    os.system(cmd)
    cmd = f"screen -S {session_id} -X log on"
    os.system(cmd)
    cmd = f"screen -S {session_id} -X colon 'logfile flush 0^M'"
    os.system(cmd)


def tail_screen_log(session, sid, stop_signal):
    log_file_path = os.path.join(LOG_ROOT, f"{session}.log")
    # if not exists, enable logging
    if not os.path.exists(log_file_path):
        enable_logging(session)
        time.sleep(0.5)
    with open(log_file_path, "r") as log_file:
        for line in tailer.follow(log_file):
            if stop_signal.is_set():
                break
            socketio.emit("command_output", {"output": line}, room=sid)


@app.route("/")
def index():
    sessions = get_screen_sessions()
    return render_template("index.html", sessions=sessions)


@socketio.on("input")
def on_input(data):
    command = data["input"].strip()
    session = data["session"].split(".")[1]

    if command not in load_whitelist():
        print(f"Command not in whitelist: {command}")
        return

    cmd = f'screen -S {session} -p 0 -X stuff "{command}^M"'
    os.system(cmd)


@socketio.on("connect")
def on_connect():
    sid = request.sid  # Get the session ID
    join_room(sid)  # Join the room for the client
    sessions = get_screen_sessions()
    emit("sessions_list", {"sessions": sessions}, room=sid)


@socketio.on("switch_session")
def on_switch_session(data):
    global session_output_tasks

    sid = request.sid
    session = data["session"]

    # Ensure the client is in the correct room
    join_room(sid)

    # Stop any existing task
    if sid in session_output_tasks:
        session_output_tasks[sid]()
        session_output_tasks.pop(sid)

    # Immediately send the last part of the log file
    log_file_path = os.path.join(LOG_ROOT, f"{session}.log")
    try:
        if not os.path.exists(log_file_path):
            enable_logging(session)
            time.sleep(1)
        initial_output = subprocess.check_output(
            f"tail -n 100 {LOG_ROOT}/{session}.log", shell=True
        ).decode("utf-8", "ignore")
        emit("command_output", {"output": initial_output}, room=sid)
    except Exception as e:
        print(f"Error sending initial output for {session}: {e}")

    # Start the background task for real-time updates
    stop_thread = threading.Event()
    thread = threading.Thread(target=tail_screen_log, args=(session, sid, stop_thread))
    thread.start()

    def stop_task():
        stop_thread.set()

    session_output_tasks[sid] = stop_task


@socketio.on("create_session")
def on_create_session(data):
    session = data["session"]
    try:
        # Create a new screen session
        subprocess.check_output(
            f"screen -dmS {session}",
            shell=True,
        )

        # get full session name and ID
        sessions = get_screen_sessions()
        session = [s for s in sessions if session in s][0]

        # enable logging
        enable_logging(session)

        # Emit a 'session_created' event back to the client
        emit("session_created", {"session": session})
    except subprocess.CalledProcessError as e:
        print(f"Error creating screen session: {e}")


# kill session
@socketio.on("kill_session")
def on_kill_session(data):
    session = data["session"]
    session_id = session.split(".")[0]
    try:
        # Create a new screen session
        subprocess.check_output(
            f"screen -X -S {session_id} quit",
            shell=True,
        )
        # Emit a 'session_created' event back to the client
        emit("session_killed", {"session": session})
    except subprocess.CalledProcessError as e:
        print(f"Error killing screen session: {e}")


# clear session, clear input by removing contents of log file
@socketio.on("clear_session")
def on_clear_session(data):
    session = data["session"]
    log_file_path = os.path.join(LOG_ROOT, f"{session}.log")
    with open(log_file_path, "w") as log_file:
        log_file.write("")


if __name__ == "__main__":
    check_session_loggers()
    socketio.run(app, debug=True)
