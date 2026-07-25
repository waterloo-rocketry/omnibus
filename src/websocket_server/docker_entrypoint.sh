#!/bin/sh
# OMNIBUS_SERVER_HOST is set via ENV in the Dockerfile and read directly by
# wsgi.py (gunicorn cannot forward CLI flags to the WSGI app).
echo "Omnibus Server: $OMNIBUS_SERVER_HOST"
cd ./src/websocket_server
exec uv run --no-sync gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 wsgi:application --bind 0.0.0.0:6767 "$@"
