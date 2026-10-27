import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from autosequence import (  # noqa: E402
    AUTO_SEQUENCE_TARGET_PRESSURE_VALUE,
    AutoSequencer,
    Phase,
    PressureSample,
)

AT_TARGET = AUTO_SEQUENCE_TARGET_PRESSURE_VALUE
BELOW_TARGET = AUTO_SEQUENCE_TARGET_PRESSURE_VALUE - 1


def sequencer(time_to_fire_ms: int = 500) -> AutoSequencer:
    return AutoSequencer(time_to_fire_ms=time_to_fire_ms)


def test_fires_after_delay_when_all_conditions_hold():
    seq = sequencer(time_to_fire_ms=500)

    fire_commands = [
        seq.update(now_s, True, True, PressureSample(AT_TARGET, now_s), False)
        for now_s in (0.0, 0.25, 0.49, 0.5)
    ]

    assert fire_commands == [False, False, False, True]
    assert seq.phase is Phase.FIRED


def test_stays_fired_after_conditions_drop():
    seq = sequencer(time_to_fire_ms=0)
    assert seq.update(0.0, True, True, PressureSample(AT_TARGET, 0.0), False)

    still_firing = seq.update(1.0, False, False, None, True)

    assert still_firing


def test_does_not_fire_without_arming_or_hold():
    seq = sequencer(time_to_fire_ms=0)
    pressure = PressureSample(AT_TARGET, 0.0)

    assert not seq.update(0.0, False, True, pressure, False)
    assert not seq.update(0.0, True, False, pressure, False)
    assert seq.phase is Phase.WAITING_FOR_IGNITION


def test_does_not_fire_below_target_pressure():
    seq = sequencer(time_to_fire_ms=0)

    assert not seq.update(0.0, True, True, PressureSample(BELOW_TARGET, 0.0), False)
    assert seq.phase is Phase.WAITING_FOR_PRESSURE


def test_does_not_fire_on_missing_or_stale_pressure():
    seq = sequencer(time_to_fire_ms=0)

    assert not seq.update(10.0, True, True, None, False)
    assert not seq.update(10.0, True, True, PressureSample(AT_TARGET, 5.0), False)
    assert seq.phase is Phase.WAITING_FOR_PRESSURE


@pytest.mark.parametrize("invalid_psi", [math.nan, math.inf, -math.inf])
def test_does_not_fire_on_non_finite_pressure(invalid_psi):
    seq = sequencer(time_to_fire_ms=0)

    assert not seq.update(0.0, True, True, PressureSample(invalid_psi, 0.0), False)
    assert seq.phase is Phase.WAITING_FOR_PRESSURE


def test_nan_pressure_mid_countdown_aborts_it():
    seq = sequencer(time_to_fire_ms=500)
    seq.update(0.0, True, True, PressureSample(AT_TARGET, 0.0), False)

    fired = seq.update(0.5, True, True, PressureSample(math.nan, 0.5), False)

    assert not fired
    assert seq.phase is Phase.WAITING_FOR_PRESSURE


def test_condition_dropping_mid_countdown_restarts_the_delay():
    seq = sequencer(time_to_fire_ms=500)
    pressure = PressureSample(AT_TARGET, 0.0)
    seq.update(0.0, True, True, pressure, False)

    seq.update(0.4, True, False, pressure, False)  # fire button released
    resumed = seq.update(0.5, True, True, PressureSample(AT_TARGET, 0.5), False)
    almost_there = seq.update(0.99, True, True, PressureSample(AT_TARGET, 0.99), False)
    fired = seq.update(1.0, True, True, PressureSample(AT_TARGET, 1.0), False)

    assert (resumed, almost_there, fired) == (False, False, True)


def test_pressure_dropping_mid_countdown_aborts_it(capsys):
    seq = sequencer(time_to_fire_ms=500)
    seq.update(0.0, True, True, PressureSample(AT_TARGET, 0.0), False)

    seq.update(0.3, True, True, PressureSample(BELOW_TARGET, 0.3), False)

    assert seq.phase is Phase.WAITING_FOR_PRESSURE
    assert "COUNTDOWN ABORTED" in capsys.readouterr().out


def test_reports_progress_and_firing(capsys):
    seq = sequencer(time_to_fire_ms=300)
    for now_s in (0.0, 0.1, 0.2, 0.3):
        seq.update(now_s, True, True, PressureSample(AT_TARGET, now_s), False)

    output = capsys.readouterr().out

    assert "T-" in output
    assert "FIRED" in output


def test_warns_when_qd301_is_not_reported_open_after_firing(capsys):
    seq = sequencer(time_to_fire_ms=0)
    seq.update(0.0, True, True, PressureSample(AT_TARGET, 0.0), False)
    capsys.readouterr()

    seq.update(0.5, True, True, None, False)
    assert "WARNING" not in capsys.readouterr().out

    seq.update(1.5, True, True, None, False)
    assert "WARNING" in capsys.readouterr().out

    seq.update(1.6, True, True, None, True)
    assert "QD301 OPEN" in capsys.readouterr().out
