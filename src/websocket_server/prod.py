import subprocess
import sys


def main() -> None:
    cmd = [
        sys.executable,
        "-m",
        "gunicorn",
        "-k",
        "gthread",
        "--threads",
        "100",
        "--timeout",
        "100",
        "websocket_server.wsgi:application",
    ]

    result = subprocess.run(cmd)
    raise SystemExit(result.returncode)
