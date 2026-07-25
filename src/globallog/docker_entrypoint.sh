#!/bin/sh
# OMNIBUS_SERVER_HOST default is set via ENV in the Dockerfile.
echo "Omnibus Server: $OMNIBUS_SERVER_HOST"
exec uv run --no-sync ./src/globallog/main.py --quiet --omnibus-server-host "$OMNIBUS_SERVER_HOST" "$@"
