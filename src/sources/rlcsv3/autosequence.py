from dataclasses import dataclass
from enum import Enum, auto

# Name of the pressure transducer to watch, exactly as it appears in the DAQ data.
AUTO_SEQUENCE_PT_NAME = "PLACEHOLDER-PT: replace with the PT name from the DAQ config"
AUTO_SEQUENCE_TARGET_PRESSURE_VALUE = 40  # PSI
# How long both fire conditions must keep holding before QD301 is opened.
AUTO_SEQUENCE_TIME_TO_FIRE_MS = 500

MAX_PRESSURE_SAMPLE_AGE_S = 1.0
COUNTDOWN_PRINT_INTERVAL_S = 0.1
QD301_CONFIRMATION_GRACE_S = 1.0


class Phase(Enum):
    WAITING_FOR_IGNITION = auto()
    WAITING_FOR_PRESSURE = auto()
    COUNTING_DOWN = auto()
    FIRED = auto()


@dataclass(frozen=True)
class PressureSample:
    psi: float
    received_at_s: float  # same clock as the `now_s` passed to AutoSequencer.update


class AutoSequencer:
    """Decides when to open QD301: ignition armed and held, and the PT at target pressure,
    for `time_to_fire_ms`. Once fired it stays fired.

    Time is passed in by the caller (seconds, any monotonic clock), so the logic is
    deterministic and does no I/O other than printing progress.
    """

    def __init__(self,
                 target_pressure_psi: float = AUTO_SEQUENCE_TARGET_PRESSURE_VALUE,
                 time_to_fire_ms: int = AUTO_SEQUENCE_TIME_TO_FIRE_MS):
        self.target_pressure_psi = target_pressure_psi
        self.time_to_fire_s = time_to_fire_ms / 1000
        self.phase = Phase.WAITING_FOR_IGNITION
        self._last_message = ""
        self._countdown_started_at_s = 0.0
        self._last_countdown_print_s = 0.0
        self._fired_at_s = 0.0
        self._last_unconfirmed_warning_s = 0.0
        self._qd301_confirmed = False
        print("[AUTO-SEQUENCE] Waiting for ignition to be armed and held.")

    def update(self, now_s: float, armed: bool, ignition_held: bool,
               pressure: PressureSample | None, qd301_reported_open: bool) -> bool:
        """Advance the sequence. Returns True while QD301 should be commanded open."""
        if self.phase is Phase.FIRED:
            self._report_qd301_confirmation(now_s, qd301_reported_open)
            return True

        missing_ignition = [name for name, ok in (("armed", armed), ("held", ignition_held))
                            if not ok]
        if missing_ignition:
            self._enter(Phase.WAITING_FOR_IGNITION,
                        f"Ignition not {' and '.join(missing_ignition)}.")
            return False

        if pressure is None or now_s - pressure.received_at_s > MAX_PRESSURE_SAMPLE_AGE_S:
            self._enter(Phase.WAITING_FOR_PRESSURE, "No recent pressure reading.")
            return False

        if pressure.psi < self.target_pressure_psi:
            self._enter(Phase.WAITING_FOR_PRESSURE,
                        f"Pressure {pressure.psi:.1f} PSI below target "
                        f"{self.target_pressure_psi} PSI.")
            return False

        if self.phase is not Phase.COUNTING_DOWN:
            self._countdown_started_at_s = now_s
            self._last_countdown_print_s = now_s
            self._enter(Phase.COUNTING_DOWN,
                        f"Armed, held, {pressure.psi:.1f} PSI at target: "
                        f"firing in {self.time_to_fire_s * 1000:.0f} ms.")

        remaining_s = self.time_to_fire_s - (now_s - self._countdown_started_at_s)
        if remaining_s <= 0:
            self._fired_at_s = now_s
            self._enter(Phase.FIRED, "FIRED: opening QD301 until this program exits.")
            return True

        if now_s - self._last_countdown_print_s >= COUNTDOWN_PRINT_INTERVAL_S:
            self._last_countdown_print_s = now_s
            print(f"[AUTO-SEQUENCE] T-{remaining_s * 1000:.0f} ms")
        return False

    def _enter(self, phase: Phase, message: str):
        """Print the message on a change of phase, or a change of reason while waiting."""
        if phase is self.phase and message == self._last_message:
            return
        if self.phase is Phase.COUNTING_DOWN and phase is not Phase.FIRED:
            message = f"COUNTDOWN ABORTED. {message}"
        self.phase = phase
        self._last_message = message
        print(f"[AUTO-SEQUENCE] {message}")

    def _report_qd301_confirmation(self, now_s: float, qd301_reported_open: bool):
        if qd301_reported_open:
            if not self._qd301_confirmed:
                self._qd301_confirmed = True
                print("[AUTO-SEQUENCE] RLCS reports QD301 OPEN.")
            return
        self._qd301_confirmed = False
        since_fired_s = now_s - self._fired_at_s
        if (since_fired_s > QD301_CONFIRMATION_GRACE_S
                and now_s - self._last_unconfirmed_warning_s >= QD301_CONFIRMATION_GRACE_S):
            self._last_unconfirmed_warning_s = now_s
            print(f"[AUTO-SEQUENCE] WARNING: QD301 not reported OPEN "
                  f"{since_fired_s:.1f} s after firing.")
