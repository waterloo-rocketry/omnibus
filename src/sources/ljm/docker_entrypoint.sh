#!/bin/sh                                                                                                                                                                                                
OM_HOST="${OMNIBUS_SERVER_HOST:-localhost}"
cp /config/config.py ./src/sources/ljm/config.py
echo $OM_HOST
exec uv run --no-sync ./src/sources/ljm/main.py <<EOF
$OM_HOST
EOF

