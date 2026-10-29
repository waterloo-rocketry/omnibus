import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from pressure_feed import PressureFeed, average_pressure_psi  # noqa: E402

DAQ_PAYLOAD = {"data": {"PT-1 (psi)": [1.0, 2.5, 59.5], "PT-2 (psi)": []}}


def test_averages_the_readings_of_the_named_pt():
    assert average_pressure_psi(DAQ_PAYLOAD, "PT-1 (psi)") == 21.0


def test_no_reading_for_missing_or_empty_pt():
    assert average_pressure_psi(DAQ_PAYLOAD, "PT-2 (psi)") is None
    assert average_pressure_psi(DAQ_PAYLOAD, "PT-9 (psi)") is None


@pytest.mark.parametrize("readings", [[1.0, math.nan], [math.inf], [math.inf, -math.inf]])
def test_no_reading_when_the_mean_is_not_finite(readings):
    assert average_pressure_psi({"data": {"PT-1 (psi)": readings}}, "PT-1 (psi)") is None


def test_invalid_message_clears_the_previous_sample():
    feed = PressureFeed("PT-1 (psi)")
    feed.record(DAQ_PAYLOAD)
    assert feed.latest is not None and feed.latest.psi == 21.0

    feed.record({"data": {"PT-1 (psi)": [math.nan]}})

    assert feed.latest is None
