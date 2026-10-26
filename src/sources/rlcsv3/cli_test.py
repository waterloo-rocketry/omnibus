import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from autosequence import AUTO_SEQUENCE_TIME_TO_FIRE_MS  # noqa: E402
from cli import parse_args  # noqa: E402


def test_auto_sequence_is_off_by_default():
    assert not parse_args(["/dev/ttyACM0"]).auto_sequence


def test_auto_sequence_uses_default_delay_unless_overridden():
    assert (parse_args(["/dev/ttyACM0", "--auto-sequence"]).auto_sequence_time_ms
            == AUTO_SEQUENCE_TIME_TO_FIRE_MS)
    args = parse_args(["/dev/ttyACM0", "--auto-sequence", "--auto-sequence-time-ms", "250"])
    assert args.auto_sequence_time_ms == 250


@pytest.mark.parametrize("argv", [
    ["/dev/ttyACM0", "--auto-sequence-time-ms", "250"],
    ["/dev/ttyACM0", "--auto-sequence", "--auto-sequence-time-ms", "-1"],
    ["/dev/ttyACM0", "--auto-sequence", "--auto-sequence-time-ms", "soon"],
    ["/dev/ttyACM0", "--auto-sequence", "--solo"],
    ["-", "--auto-sequence"],
])
def test_rejects_invalid_auto_sequence_options(argv):
    with pytest.raises(SystemExit):
        parse_args(argv)
