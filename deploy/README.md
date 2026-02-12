# Omnibus Docker Compose Deployment

This directory contains a Docker Compose file for running the full Omnibus stack.

## Services

- **omnibus-server** — The central Omnibus message bus server.
- **omnibus-globallog** — Logs all messages passing through the bus to timestamped binary files.
- **omnibus-source-ljm** — LabJack data source.

All services use host networking (`network_mode: host`).

## Getting Started

1. **Configure the LJM source.** Copy the example config and modify it for your setup:

   ```sh
   mkdir -p config
   cp ../src/sources/ljm/config.py.example config/config.py
   ```

   Edit `config/config.py` to match your sensor calibrations and LabJack port configuration. See `src/sources/ljm/config.py.example` for documentation.

2. **Start the stack:**

   ```sh
   docker compose up
   ```

   Globallog data will be written to the `data/` directory.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OMNIBUS_SERVER_HOST` | `localhost` | Hostname of the Omnibus server. Used by `omnibus-globallog` and `omnibus-source-ljm` to connect to the bus. |

Example:

```sh
OMNIBUS_SERVER_HOST=192.168.1.100 docker compose up
```

## Volumes

| Service | Host Path | Container Path | Purpose |
|---|---|---|---|
| `omnibus-globallog` | `./data` | `/data` | Log output directory |
| `omnibus-source-ljm` | `./config` | `/config` | LJM `config.py` |
