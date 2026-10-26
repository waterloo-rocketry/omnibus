import threading
import time
from typing import Any

from omnibus import Receiver

from autosequence import PressureSample

DAQ_CHANNEL = "DAQ"
FIRST_MESSAGE_TIMEOUT_MS = 10_000
RECEIVE_TIMEOUT_MS = 1000


def latest_pressure_psi(daq_payload: Any, pt_name: str) -> float | None:
    """The newest reading of `pt_name` in a DAQ message, or None if the message has none."""
    readings = daq_payload["data"].get(pt_name)
    return readings[-1] if readings else None


class PressureFeed:
    def __init__(self, pt_name: str):
        self._pt_name = pt_name
        self._receiver = Receiver(DAQ_CHANNEL)
        self._latest: PressureSample | None = None

    @property
    def latest(self) -> PressureSample | None:
        return self._latest

    def start(self):
        """Wait for the first DAQ message, exit if it lacks the PT, then keep reading in the
        background."""
        payload = self._receiver.recv(FIRST_MESSAGE_TIMEOUT_MS)
        if payload is None:
            raise SystemExit(f"No DAQ data received within {FIRST_MESSAGE_TIMEOUT_MS} ms; "
                             f"cannot confirm PT '{self._pt_name}'.")
        if self._pt_name not in payload["data"]:
            raise SystemExit(f"PT '{self._pt_name}' is not in the DAQ data. Available: "
                             f"{', '.join(sorted(payload['data']))}")
        self._record(payload)
        threading.Thread(target=self._read_forever, daemon=True).start()

    def _read_forever(self):
        while True:
            payload = self._receiver.recv(RECEIVE_TIMEOUT_MS)
            if payload is not None:
                self._record(payload)

    def _record(self, payload: Any):
        psi = latest_pressure_psi(payload, self._pt_name)
        if psi is not None:
            self._latest = PressureSample(psi, time.monotonic())
