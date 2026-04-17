#!/bin/sh
OM_HOST="${OMNIBUS_SERVER_HOST:-localhost}"
WS_HOST="${WS_SERVER_HOST:-127.0.0.1}"
WS_PORT="${WS_SERVER_PORT:-6767}"
echo "Omnibus Server: $OM_HOST"
echo "WebSocket Server: $WS_HOST:$WS_PORT"
exec uv run --no-sync ./src/bridge/main.py --host "$WS_HOST" --port "$WS_PORT" "$@" <<EOF
$OM_HOST
EOF
