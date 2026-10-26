"""End to end: real Omnibus server, real main.py, and a pseudo-terminal standing in for the
RLCS firmware's USB port."""
import os
import pty
import select
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import rlcs  # noqa: E402
from omnibus import Sender  # noqa: E402
from omnibus.server import SOURCE_PORT  # noqa: E402

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="needs a pseudo-terminal")

PT_NAME = "E2E-PT (psi)"
TIMEOUT_S = 20

# main.py with the PT name set and Omnibus discovery skipped (the server is on localhost).
RLCS_SOURCE = f"""
import sys
sys.path.insert(0, {str(Path(__file__).parent)!r})
from omnibus.omnibus import OmnibusCommunicator
OmnibusCommunicator.server_ip = "127.0.0.1"
import autosequence
autosequence.AUTO_SEQUENCE_PT_NAME = {PT_NAME!r}
import main
try:
    main.main()
except KeyboardInterrupt:
    pass
"""


def armed_and_held_frame() -> bytes:
    payload = bytearray(rlcs.EXPECTED_SIZE - 2)
    payload[11] = 1  # Ignition Primary Command: OPEN
    payload[19] = 1  # Towerside Armed: TRUE
    return b"W" + bytes(payload) + b"R"


def wait_for_port(port: int):
    deadline = time.time() + TIMEOUT_S
    while time.time() < deadline:
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            return
        except OSError:
            time.sleep(0.1)
    pytest.fail(f"Omnibus server did not open port {port}")


def test_fires_qd301_then_releases_it_on_exit():
    server = subprocess.Popen([sys.executable, "-c", "from omnibus.server import server; server()"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    firmware_end, source_end = pty.openpty()
    source = None
    publishing = threading.Event()
    try:
        wait_for_port(SOURCE_PORT)
        source = subprocess.Popen(
            [sys.executable, "-c", RLCS_SOURCE, os.ttyname(source_end),
             "--auto-sequence", "--auto-sequence-time-ms", "100"],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
        assert source.stdin
        source.stdin.write("FIRE QD301 AUTOMATICALLY\n")
        source.stdin.flush()

        def publish_daq():
            sender = Sender(server_ip="127.0.0.1")
            while not publishing.is_set():
                sender.send("DAQ/e2e", {"data": {PT_NAME: [45.0]}})
                time.sleep(0.05)
        threading.Thread(target=publish_daq, daemon=True).start()

        def read_until(expected_frame: bytes):
            received = b""
            deadline = time.time() + TIMEOUT_S
            while expected_frame not in received:
                assert time.time() < deadline, f"never received {expected_frame!r}"
                os.write(firmware_end, armed_and_held_frame())
                if select.select([firmware_end], [], [], 0.05)[0]:
                    received += os.read(firmware_end, 1024)

        read_until(rlcs.QD301_OVERRIDE_OPEN)
        source.send_signal(signal.SIGINT)
        read_until(rlcs.QD301_OVERRIDE_RELEASE)
        assert source.wait(TIMEOUT_S) == 0
    finally:
        publishing.set()
        if source and source.poll() is None:
            source.kill()
        server.kill()
        server.wait()
        os.close(firmware_end)
        os.close(source_end)
