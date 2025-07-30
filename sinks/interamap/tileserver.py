import subprocess
import os
import sys
import argparse

CONTAINER_NAME = "tileserver-omnibus-interamap"

def start_tileserver_with_docker(mbtiles_path):
    """Start the tileserver-gl Docker container in detached mode."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mbtiles_abs_path = os.path.abspath(os.path.join(script_dir, "resources/mbtiles", os.path.basename(mbtiles_path)))
    host_dir = os.path.dirname(mbtiles_abs_path)
    container_mbtiles_path = os.path.basename(mbtiles_abs_path)

    command = [
        "docker", "run", "--rm", "-d",  # Run in detached mode
        "--name", CONTAINER_NAME,
        "-v", f"{host_dir}:/data",
        "-p", "8080:8080",
        "maptiler/tileserver-gl",
        "--file", f"{container_mbtiles_path}"
    ]

    print(f"Starting tileserver-gl via Docker with {mbtiles_path}...")
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        container_id = result.stdout.decode().strip()
        print(f"TileServer is running in container: {container_id}")
    except subprocess.CalledProcessError as e:
        print("Failed to start TileServer:")
        print(e.stderr.decode())
        sys.exit(1)


def stop_tileserver():
    """Stop the running tileserver-gl Docker container."""
    print(f"Stopping container '{CONTAINER_NAME}'...")
    try:
        subprocess.run(["docker", "stop", CONTAINER_NAME], check=True)
        print("TileServer stopped.")
    except subprocess.CalledProcessError:
        print("No running TileServer container found or error stopping it.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start or stop tileserver-gl via Docker.")
    subparsers = parser.add_subparsers(dest="command", help="Sub-command help")

    # Start command
    parser_start = subparsers.add_parser("start", help="Start TileServer with a .mbtiles file")
    parser_start.add_argument(
        "mbtiles_file",
        nargs="?",
        default="ontario-latest.osm.mbtiles",
        help="Path to the .mbtiles file relative to project root.",
    )

    # Stop command
    subparsers.add_parser("stop", help="Stop the running TileServer container")

    args = parser.parse_args()

    if args.command == "start":
        start_tileserver_with_docker(args.mbtiles_file)
    elif args.command == "stop":
        stop_tileserver()
    else:
        parser.print_help()
