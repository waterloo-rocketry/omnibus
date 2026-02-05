#!/bin/sh
OM_HOST="${OMNIBUS_SERVER_HOST:-localhost}"
echo "Omnibus Server: $OM_HOST"
exec uv run --no-sync ./src/globallog/main.py --quiet <<EOF
$OM_HOST
EOF
