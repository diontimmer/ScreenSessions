#!/bin/bash

# Flask App Start Script

# Command-line arguments:
# -p, --port: Specify the port number to run the Flask app (default: 5000)
# -h, --host: Specify the host address to bind the Flask app (default: 0.0.0.0)
# -d, --debug: Enable debug mode for the Flask app (default: off)

# Default values
PORT=5000
HOST="0.0.0.0"
DEBUG=false

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -p|--port)
            PORT="$2"
            shift
            shift
            ;;
        -h|--host)
            HOST="$2"
            shift
            shift
            ;;
        -d|--debug)
            DEBUG=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Start the Flask app
if $DEBUG; then
    echo "Starting Flask app in debug mode..."
    FLASK_ENV=development FLASK_APP=app.py flask run --host "$HOST" --port "$PORT"
else
    echo "Starting Flask app..."
    FLASK_APP=app.py flask run --host "$HOST" --port "$PORT"
fi
