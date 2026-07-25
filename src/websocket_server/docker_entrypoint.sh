#!/bin/sh
OM_HOST="${OMNIBUS_SERVER_HOST:-localhost}"
echo "Omnibus Server: $OM_HOST"
# gunicorn cannot forward CLI flags to the WSGI app, so pass the server address
# through the environment; wsgi.py reads OMNIBUS_SERVER_HOST.
export OMNIBUS_SERVER_HOST="$OM_HOST"
cd ./src/websocket_server
exec uv run --no-sync gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 wsgi:application --bind 0.0.0.0:6767 "$@"
