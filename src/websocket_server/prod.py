import subprocess
import sys


def main() -> None:
    cmd = [
        sys.executable,
        "-m",
        "gunicorn",
        "-w",
        "1",
        "-t",
        "100",
        "websocket_server.wsgi:application",
    ]
    raise SystemExit(subprocess.call(cmd))
