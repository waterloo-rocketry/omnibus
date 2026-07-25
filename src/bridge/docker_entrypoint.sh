#!/bin/sh
# OMNIBUS_SERVER_HOST default is set via ENV in the Dockerfile.
WS_HOST="${WS_SERVER_HOST:-127.0.0.1}"
WS_PORT="${WS_SERVER_PORT:-6767}"
echo "Omnibus Server: $OMNIBUS_SERVER_HOST"
echo "WebSocket Server: $WS_HOST:$WS_PORT"
exec uv run --no-sync ./src/bridge/main.py --host "$WS_HOST" --port "$WS_PORT" --omnibus-server-host "$OMNIBUS_SERVER_HOST" "$@"
