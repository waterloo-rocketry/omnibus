#!/bin/bash

# Script to free a specified port

# Check if port number is provided as an argument
if [ $# -ne 1 ]; then
  echo "Usage: $0 <port_number>"
  exit 1
fi

PORT=$1

# Validate that the port is a number
if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
  echo "Error: Port must be a number."
  exit 1
fi

# Find processes using the specified port
PIDS=$(lsof -i :$PORT | grep LISTEN | awk '{print $2}' | uniq)

if [ -z "$PIDS" ]; then
  echo "No processes found using port $PORT."
  exit 0
fi

# Loop through each PID and kill the process
for PID in $PIDS; do
  echo "Killing process $PID using port $PORT..."
  kill -9 $PID
  if [ $? -eq 0 ]; then
    echo "Process $PID terminated successfully."
  else
    echo "Failed to terminate process $PID."
  fi
done

# Verify the port is free
if lsof -i :$PORT >/dev/null; then
  echo "Port $PORT is still in use. Please check manually."
else
  echo "Port $PORT is now free."
fi

exit 0
