import subprocess
import os
import sys
import argparse


def check_tileserver_installed():
    """Check if tileserver-gl is installed."""
    try:
        subprocess.run(
            ["tileserver-gl", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print("tileserver-gl is installed.")
    except subprocess.CalledProcessError:
        print("tileserver-gl is not installed.")
        sys.exit(1)
    except FileNotFoundError:
        print("tileserver-gl is not found. Please install it.")
        sys.exit(1)


def start_tileserver(mbtiles_path):
    """Start the tileserver-gl process."""
    # Define the command to start the tile server
    command = ["tileserver-gl", "resources/mbtiles/" + mbtiles_path]

    # Start the subprocess
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print(f"Starting tileserver-gl with {mbtiles_path}...")

    # Capture the output and errors
    stdout, stderr = process.communicate()

    # Print the output and errors
    print("Output:", stdout.decode())
    print("Errors:", stderr.decode())


def run_tileserver(mbtiles_path):
    """Main function to check tileserver installation and start it."""
    try:
        check_tileserver_installed()
        start_tileserver(mbtiles_path)
    except Exception as e:
        print(f"Error: {e}")


# Main entry point for running the module
if __name__ == "__main__":
    # Argument parsing
    parser = argparse.ArgumentParser(
        description="Start tileserver-gl with a specific .mbtiles file."
    )
    parser.add_argument(
        "mbtiles_file",
        nargs="?",
        default="ontario-latest.osm.mbtiles",
        help="The path to the .mbtiles file",
    )
    args = parser.parse_args()

    # Run the tileserver with the provided .mbtiles file
    run_tileserver(args.mbtiles_file)
