#!/bin/sh                                                                                                                                                                                                
OM_HOST="${OMNIBUS_SERVER_HOST:-localhost}"
cp /config/config.py ./src/sources/ljm/config.py || exit $?
echo "Omnibus Server: $OM_HOST"
exec uv run --no-sync ./src/sources/ljm/main.py --quiet --no-built-in-log <<EOF
$OM_HOST
EOF

