import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pressure_feed import average_pressure_psi  # noqa: E402

DAQ_PAYLOAD = {"data": {"PT-1 (psi)": [1.0, 2.5, 59.5], "PT-2 (psi)": []}}


def test_averages_the_readings_of_the_named_pt():
    assert average_pressure_psi(DAQ_PAYLOAD, "PT-1 (psi)") == 21.0


def test_no_reading_for_missing_or_empty_pt():
    assert average_pressure_psi(DAQ_PAYLOAD, "PT-2 (psi)") is None
    assert average_pressure_psi(DAQ_PAYLOAD, "PT-9 (psi)") is None
