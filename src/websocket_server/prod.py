import subprocess
import sys
from unittest import result


def main() -> None:
    cmd = [
        sys.executable,
        "-m",
        "gunicorn",
        "-w",
        "1",
        "-k",
        "gthread",
        "--threads",
        "100",
        "-t",
        "100",
        "websocket_server.wsgi:application",
    ]
    
    result = subprocess.run(cmd)
    raise SystemExit(result.returncode)
