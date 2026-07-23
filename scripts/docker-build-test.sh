#!/usr/bin/env bash
#
# Build and smoke-test the Omnibus Docker images using docker compose.
#
# What this proves
# ----------------
# The source/sink Docker entrypoints now pass the Omnibus server address as a
# CLI flag (`--omnibus-server-host`) instead of piping it through stdin.
# (The websocket server and bridge are intentionally left on their original
# stdin/auto-discovery flow.)
#
# This script drives the real deploy/docker-compose.yml topology, layered with
# deploy/docker-compose.local.yml so the images are built locally from source
# instead of pulled from ghcr.io. It then:
#   1. builds every image (acceptance: "containers build"),
#   2. brings up the server + sinks/relays,
#   3. publishes a probe message and confirms the globallog sink recorded it
#      (acceptance: "sinks connect via the CLI-passed address"),
#   4. asserts no container fell back to the "Listening for server IP..."
#      discovery/stdin path,
#   5. optionally starts the ljm source to show it, too, takes the address from
#      the flag (it then fails on missing LabJack hardware, as expected).
#
# Usage:
#   scripts/docker-build-test.sh [options]
#
# Options:
#   --no-build   Skip building; reuse existing local images.
#   --skip-ljm   Do not build/run the ljm source image (large, arch-specific
#                download; needs a physical LabJack T7 to actually run).
#   --keep       Leave the stack running afterwards for manual poking.
#   -h, --help   Show this help.
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE="deploy/docker-compose.yml"
OVERRIDE="deploy/docker-compose.local.yml"
DATA_DIR="${REPO_ROOT}/deploy/data"
CONFIG_DIR="${REPO_ROOT}/deploy/config"
PROBE_CHANNEL="DAQ/probe"

DO_BUILD=1
SKIP_LJM=0
KEEP=0

# Services to run for the functional test (ljm excluded: needs hardware).
RUN_SERVICES="omnibus-server omnibus-globallog omnibus-ws-server omnibus-ws-bridge"

# --- pretty logging -------------------------------------------------------- #
if [ -t 1 ]; then
  C_BLUE="\033[34m"; C_GREEN="\033[32m"; C_RED="\033[31m"; C_YELLOW="\033[33m"; C_RST="\033[0m"
else
  C_BLUE=""; C_GREEN=""; C_RED=""; C_YELLOW=""; C_RST=""
fi
step() { printf "\n${C_BLUE}==>${C_RST} %s\n" "$*"; }
info() { printf "    %s\n" "$*"; }
ok()   { printf "${C_GREEN}  ✓ %s${C_RST}\n" "$*"; }
warn() { printf "${C_YELLOW}  ! %s${C_RST}\n" "$*"; }
fail() { printf "${C_RED}  ✗ %s${C_RST}\n" "$*"; }

# --- args ------------------------------------------------------------------ #
while [ $# -gt 0 ]; do
  case "$1" in
    --no-build) DO_BUILD=0 ;;
    --skip-ljm) SKIP_LJM=1 ;;
    --keep)     KEEP=1 ;;
    -h|--help)  sed -n '2,40p' "$0"; exit 0 ;;
    *) fail "Unknown option: $1"; exit 2 ;;
  esac
  shift
done

cd "${REPO_ROOT}"
dc() { docker compose -f "${BASE}" -f "${OVERRIDE}" "$@"; }

# --- cleanup --------------------------------------------------------------- #
cleanup() {
  if [ "$KEEP" -eq 1 ]; then
    warn "--keep set: leaving the stack running."
    info "Tear down later with:"
    info "  docker compose -f ${BASE} -f ${OVERRIDE} down"
    info "  rm -rf deploy/data deploy/config"
    return
  fi
  step "Cleaning up"
  dc down >/dev/null 2>&1 || true
  rm -rf "${DATA_DIR}" "${CONFIG_DIR}" >/dev/null 2>&1 || true
  ok "Stack down; test data/config removed."
}
trap cleanup EXIT

# --- preflight ------------------------------------------------------------- #
step "Preflight"
if ! docker info >/dev/null 2>&1; then
  fail "Docker daemon is not reachable. Start Docker/OrbStack/Colima and retry."
  exit 1
fi
ok "Docker daemon reachable."
dc down >/dev/null 2>&1 || true
rm -rf "${DATA_DIR}" "${CONFIG_DIR}"

# --- build ----------------------------------------------------------------- #
if [ "$DO_BUILD" -eq 1 ]; then
  step "Building images via compose"
  if [ "$SKIP_LJM" -eq 1 ]; then
    dc build ${RUN_SERVICES}
    warn "Skipped building omnibus-source-ljm (--skip-ljm)."
  else
    dc build
  fi
  ok "Images built."
else
  warn "--no-build set: reusing existing local images."
fi

# --- run stack ------------------------------------------------------------- #
step "Starting stack (server + sinks/relays)"
dc up -d ${RUN_SERVICES} >/dev/null
info "Waiting for components to connect..."
sleep 5
dc ps

# --- probe ----------------------------------------------------------------- #
step "Publishing a probe message through the ZMQ pipeline"
PROBE_PY="$(mktemp -t omnibus-probe.XXXXXX).py"
cat > "${PROBE_PY}" <<PYEOF
import time
from omnibus import Sender
s = Sender("localhost")  # explicit address, same value the entrypoint flag uses
for n in range(80):
    s.send("${PROBE_CHANNEL}", {"probe": f"hello {n}", "n": n})
    time.sleep(0.05)
print("probe: sent 80 messages to localhost")
PYEOF
# network_mode: host in compose -> reach the server on localhost.
docker run --rm --network host -v "${PROBE_PY}:/probe.py:ro" \
  --entrypoint uv omnibus-server:local run --no-sync python /probe.py
rm -f "${PROBE_PY}"

info "Stopping globallog to flush its log buffer..."
dc stop omnibus-globallog >/dev/null

# --- verify ---------------------------------------------------------------- #
step "Verifying"
PASS=1

for svc in omnibus-globallog omnibus-ws-bridge; do
  if dc logs "$svc" 2>&1 | grep -q "Omnibus Server:"; then
    ok "$svc received address via entrypoint: $(dc logs "$svc" 2>&1 | grep 'Omnibus Server:' | tail -1 | sed 's/.*| //')"
  else
    warn "$svc did not echo 'Omnibus Server:'."
  fi
done

if dc logs omnibus-globallog 2>&1 | grep -q "Listening for server IP"; then
  fail "globallog fell back to discovery/stdin ('Listening for server IP')."
  PASS=0
else
  ok "globallog did not use discovery/stdin (took the CLI-flag path)."
fi

if grep -aql "${PROBE_CHANNEL}" "${DATA_DIR}"/*.log 2>/dev/null; then
  ok "globallog recorded '${PROBE_CHANNEL}' -> sink connected via the flag address."
else
  fail "No '${PROBE_CHANNEL}' found in globallog output under ${DATA_DIR}."
  dc logs omnibus-globallog 2>&1 | tail -20
  PASS=0
fi

# --- ljm source demo (informational; needs real hardware to fully run) ----- #
if [ "$SKIP_LJM" -eq 0 ]; then
  step "Demonstrating the ljm source reads the address from the flag"
  mkdir -p "${CONFIG_DIR}"
  cp src/sources/ljm/config.py.example "${CONFIG_DIR}/config.py"
  dc up -d omnibus-source-ljm >/dev/null
  sleep 5
  info "ljm logs (expect 'Omnibus Server: localhost' then a LabJack hardware error):"
  dc logs omnibus-source-ljm 2>&1 | tail -6
  if dc logs omnibus-source-ljm 2>&1 | grep -q "Listening for server IP"; then
    fail "ljm fell back to discovery/stdin."
    PASS=0
  else
    ok "ljm took the CLI-flag path (no discovery); hardware error is expected without a T7."
  fi
fi

# --- summary --------------------------------------------------------------- #
echo
if [ "$PASS" -eq 1 ]; then
  printf "${C_GREEN}==================== ALL CHECKS PASSED ====================${C_RST}\n"
  exit 0
else
  printf "${C_RED}==================== SOME CHECKS FAILED ===================${C_RST}\n"
  exit 1
fi
