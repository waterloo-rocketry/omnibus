#!/bin/sh
OM_HOST="${OMNIBUS_SERVER_HOST:-localhost}"
echo "Omnibus Server: $OM_HOST"
cd ./src/websocket_server
exec uv run --no-sync gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 wsgi:application --bind 0.0.0.0:6767 "$@" <<EOF
$OM_HOST
EOF
