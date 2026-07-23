# Manually Building & Testing the Omnibus Docker Images

This guide shows how to build every Omnibus container image and verify that the
**sources/sinks** connect to the Omnibus server through the CLI flag
(`--omnibus-server-host`) rather than by piping the address through `stdin`.

It uses the real [`deploy/docker-compose.yml`](../deploy/docker-compose.yml)
topology, layered with
[`deploy/docker-compose.local.yml`](../deploy/docker-compose.local.yml) so the
images are **built locally from source** instead of pulled from `ghcr.io`.

A helper script, [`scripts/docker-build-test.sh`](./docker-build-test.sh),
automates all of it. This document explains the same steps so you can run them
by hand.

## Scope of the change being tested

| Component            | Address source                     | Changed?             |
| -------------------- | ---------------------------------- | -------------------- |
| `omnibus-globallog`  | `--omnibus-server-host` CLI flag   | ✅ yes (sink)         |
| `omnibus-source-ljm` | `--omnibus-server-host` CLI flag   | ✅ yes (source)       |
| `omnibus-ws-server`  | original stdin / auto-discovery    | left untouched       |
| `omnibus-ws-bridge`  | original stdin / auto-discovery    | left untouched       |
| `omnibus-server`     | n/a (it *is* the server)           | n/a                  |

## TL;DR

```bash
# From the repo root. Builds all images, runs a smoke test, cleans up.
./scripts/docker-build-test.sh

# Skip the ljm image (large arch-specific download; needs a LabJack T7 to run):
./scripts/docker-build-test.sh --skip-ljm

# Reuse already-built images and leave the stack up to poke at:
./scripts/docker-build-test.sh --no-build --keep
```

Exit code `0` / `ALL CHECKS PASSED` means the images build and the sink
connects via the passed-in address.

## Prerequisites

- Docker (or OrbStack/Colima) with a **running daemon** — verify with
  `docker info`.
- Run from the **repo root**. Every Dockerfile uses the repo root as its build
  context (`COPY . /app`); the build override sets `context: ..` accordingly.

## Manual steps (what the script does)

Define a shortcut for the layered compose invocation:

```bash
dc() { docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.local.yml "$@"; }
```

### 1. Build every image

```bash
dc build
```

The override tags them `omnibus-server:local`, `omnibus-globallog:local`,
`omnibus-ws-server:local`, `omnibus-ws-bridge:local`, `omnibus-source-ljm:local`.

✅ *Acceptance criterion 1: the containers build.*

### 2. Start the server + sinks/relays

The ljm source is left out here because it needs a physical LabJack T7.

```bash
dc up -d omnibus-server omnibus-globallog omnibus-ws-server omnibus-ws-bridge
dc ps
```

`globallog`'s log should show `Omnibus Server: localhost` — its entrypoint
resolves `OMNIBUS_SERVER_HOST` (default `localhost`, since compose uses
`network_mode: host`) and passes it as `--omnibus-server-host`.

### 3. Push a message through the pipeline

Run a throwaway `Sender` (the `omnibus` package ships in the server image) that
connects using the explicit address and publishes some messages. Because compose
uses host networking, reach the server on `localhost`:

```bash
docker run --rm --network host --entrypoint uv omnibus-server:local \
  run --no-sync python -c '
import time
from omnibus import Sender
s = Sender("localhost")
for n in range(80):
    s.send("DAQ/probe", {"probe": "hello", "n": n})
    time.sleep(0.05)
print("sent")'
```

### 4. Verify the sink received it

`globallog` block-buffers its file, so stop it to flush, then inspect the log
that landed in the `./data` volume (mapped to `deploy/data`):

```bash
dc stop omnibus-globallog
grep -al "DAQ/probe" deploy/data/*.log && echo "END-TO-END OK"
```

Also confirm the sink never fell back to discovery/stdin:

```bash
dc logs omnibus-globallog | grep -c "Listening for server IP"   # expect 0
```

Finding `DAQ/probe` proves a **Sender** and the **globallog Receiver** both
reached the server via the passed-in address.

✅ *Acceptance criterion 2: the sink connects via the CLI-passed address.*

### 5. (Optional) Show the ljm source uses the flag

Without a LabJack T7 the source can't stream, but you can confirm it takes the
address from the flag: it constructs its `Sender` *before* opening the device,
so it logs the server address and then fails on the hardware step.

```bash
mkdir -p deploy/config
cp src/sources/ljm/config.py.example deploy/config/config.py
dc up -d omnibus-source-ljm
dc logs omnibus-source-ljm | tail
# -> "Omnibus Server: localhost"
# -> "Error handling LabJack device: ... LJME_DEVICE_NOT_FOUND"   (expected, no T7)
```

To run it for real with hardware attached, provide a real `deploy/config/config.py`
and pass the device through — the compose service already mounts `./config` and
uses host networking; add your device with a compose override or `docker run
--device /dev/ttyACM0 ...`.

### 6. Clean up

```bash
dc down
rm -rf deploy/data deploy/config
```

## Troubleshooting

- **`Docker daemon is not reachable`** — start Docker Desktop / OrbStack /
  Colima, then re-run. Check with `docker info`.
- **A build fails on `uv sync --locked`** — the lockfile is stale relative to
  `pyproject.toml`; run `uv lock` and rebuild.
- **`No 'DAQ/probe' found`** — inspect `dc logs omnibus-globallog`. A
  `Listening for server IP...` line means the address was not passed through
  (regression); otherwise it's likely a timing/flush issue — re-run.
- **ljm build fails with "Unsupported architecture"** — only linux/amd64 and
  linux/arm64 LJM downloads are wired up; use `--skip-ljm` elsewhere.
