import math
import threading
import time
from typing import Any

from omnibus import Receiver

from autosequence import PressureSample

DAQ_CHANNEL = "DAQ"
FIRST_MESSAGE_TIMEOUT_MS = 10_000
RECEIVE_TIMEOUT_MS = 1000


def average_pressure_psi(daq_payload: Any, pt_name: str) -> float | None:
    """The mean of `pt_name`'s readings in a DAQ message, to smooth out sensor noise, or None
    if the message has none or the mean is not a finite number."""
    readings = daq_payload["data"].get(pt_name)
    if not readings:
        return None
    mean = sum(readings) / len(readings)
    return mean if math.isfinite(mean) else None


class PressureFeed:
    def __init__(self, pt_name: str):
        self._pt_name = pt_name
        self._latest: PressureSample | None = None

    @property
    def latest(self) -> PressureSample | None:
        return self._latest

    def start(self):
        """Wait for the first DAQ message, exit if it lacks the PT, then keep reading in the
        background."""
        receiver = Receiver(DAQ_CHANNEL)
        payload = receiver.recv(FIRST_MESSAGE_TIMEOUT_MS)
        if payload is None:
            raise SystemExit(f"No DAQ data received within {FIRST_MESSAGE_TIMEOUT_MS} ms; "
                             f"cannot confirm PT '{self._pt_name}'.")
        if self._pt_name not in payload["data"]:
            raise SystemExit(f"PT '{self._pt_name}' is not in the DAQ data. Available: "
                             f"{', '.join(sorted(payload['data']))}")
        self.record(payload)
        threading.Thread(target=self._read_forever, args=(receiver,), daemon=True).start()

    def _read_forever(self, receiver: Receiver):
        while True:
            payload = receiver.recv(RECEIVE_TIMEOUT_MS)
            if payload is not None:
                self.record(payload)

    def record(self, payload: Any):
        """Replace the latest sample; a message without a valid reading clears it."""
        psi = average_pressure_psi(payload, self._pt_name)
        self._latest = None if psi is None else PressureSample(psi, time.monotonic())
