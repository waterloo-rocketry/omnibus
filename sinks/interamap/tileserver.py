#!/usr/bin/env python3
"""
tileserver_ctl.py – Start or stop a tileserver-gl container via the Docker SDK
"""

import os
import sys
import argparse
import docker
from docker.errors import NotFound, APIError
from docker.client import DockerClient

CONTAINER_NAME = "tileserver-omnibus-interamap"
IMAGE_NAME = "maptiler/tileserver-gl"
HOST_PORT = 8080
CONTAINER_PORT = "8080/tcp"


def start_tileserver(mbtiles_path: str) -> None:
    """
    Start (or replace) a tileserver-gl container in detached mode,
    serving the given .mbtiles file.
    """
    # Resolve absolute paths
    script_dir: str = os.path.dirname(os.path.abspath(__file__))
    mbtiles_abs_path: str = os.path.abspath(
        os.path.join(script_dir, "resources/mbtiles", os.path.basename(mbtiles_path))
    )
    host_dir: str = os.path.dirname(mbtiles_abs_path)
    container_mbtiles = os.path.basename(mbtiles_abs_path)

    client: DockerClient = docker.from_env()

    # If a container with this name exists, remove it first so we can start fresh
    try:
        old = client.containers.get(CONTAINER_NAME)
        print(f"A container named {CONTAINER_NAME} already exists – removing it…")
        old.remove(force=True)
    except NotFound:
        pass  # Nothing to remove

    print(f"Starting {IMAGE_NAME} with {container_mbtiles}…")

    try:
        container = client.containers.run(
            IMAGE_NAME,
            name=CONTAINER_NAME,
            detach=True,
            remove=True,  # equivalent to `--rm`
            volumes={host_dir: {"bind": "/data", "mode": "ro"}},
            ports={CONTAINER_PORT: HOST_PORT},
            command=["--file", container_mbtiles],
        )
        print(f"TileServer is running in container: {container.id[:12]}")
        print(f"Visit http://localhost:{HOST_PORT}/")
    except APIError as err:
        print("Failed to start TileServer:")
        print(err.explanation)
        sys.exit(1)


def stop_tileserver() -> None:
    """
    Stop the running tileserver-gl container, if any.
    """
    client = docker.from_env()
    try:
        container = client.containers.get(CONTAINER_NAME)
        print(f"Stopping container '{CONTAINER_NAME}'…")
        container.stop()
        # If `remove=True` was set at run-time the container is already gone.
        print("TileServer stopped.")
    except NotFound:
        print("No running TileServer container found.")
    except APIError as err:
        print("Error stopping TileServer:")
        print(err.explanation)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Start or stop tileserver-gl via the Docker SDK."
    )
    subparsers = parser.add_subparsers(dest="command")

    # Start
    parser_start = subparsers.add_parser("start", help="Start TileServer")
    parser_start.add_argument(
        "mbtiles_file",
        nargs="?",
        default="ontario-latest.osm.mbtiles",
        help="Path to the .mbtiles file (relative to project root).",
    )

    # Stop
    subparsers.add_parser("stop", help="Stop TileServer")

    args = parser.parse_args()

    if args.command == "start":
        start_tileserver(args.mbtiles_file)
    elif args.command == "stop":
        stop_tileserver()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
