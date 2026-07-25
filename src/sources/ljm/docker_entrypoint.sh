#!/bin/sh
# OMNIBUS_SERVER_HOST default is set via ENV in the Dockerfile.
cp /config/config.py ./src/sources/ljm/config.py || exit $?
echo "Omnibus Server: $OMNIBUS_SERVER_HOST"
exec uv run --no-sync ./src/sources/ljm/main.py --quiet --no-built-in-log --omnibus-server-host "$OMNIBUS_SERVER_HOST" "$@"
