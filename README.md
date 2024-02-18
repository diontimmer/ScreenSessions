# ScreenSessions
Flask Web UI for GNU Screen. List, create, and kill screen sessions in a graphical interface (GUI).<br>

![img](https://www.dropbox.com/scl/fi/c49hyqu40225o8kxgibex/screensessions.png?rlkey=b7o71pshizb2hx207l02nvlep&raw=1)

## What does it do?
This tool is used to monitor various GNU screen sessions remotely through a nice user interface. i have found myself opening many tabs of console windows  and have been trying to find a nice, clean and easy solution which wraps around Screen. This utility will enable logging on your current screen sessions, pipe it to a tmp folder, which sends it  to these xterm components for you to view. Command execution is completely optional and at your own risk, only 'ls' is activated as an example command.

## Installation
- Install requirements.txt using your Python interpreter of choice by running ```pip install -r requirements``` with your environment activated.
- Run it as a flask app by running the command: ```flask run``` in the script root folder, or by simply running the start.sh script file. The start script file can be populated with the arguments described below.

If you're feeling risky, you can whitelist scripts/commands in the config.json for you to run in the containers. DO THIS AT YOUR OWN RISK! No wildcard system is implemented for this, only exactly whitelisted commands will run. This system could be used to run pre-set user scripts.<br><br>
Flask has arguments which you can append to the startup command for more control, such as ```--host <ip>``` for a custom host, ```--port <port>``` for a custom port or ```--cert <certificate>``` for local https support.
