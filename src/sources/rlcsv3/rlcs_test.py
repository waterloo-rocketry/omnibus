import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import rlcs  # noqa: E402


@pytest.mark.parametrize("qd301_override, qd301_command, frame", [
    ("OVERRIDE", "OPEN", b"W\x01\x01R"),
    ("OVERRIDE", "CLOSED", b"W\x01\x00R"),
    ("RELEASED", "CLOSED", b"W\x00\x00R"),
])
def test_override_frames_match_the_firmware_wire_format(qd301_override, qd301_command, frame):
    assert rlcs.encode_override(qd301_override, qd301_command) == frame


def test_open_and_release_constants():
    assert rlcs.QD301_OVERRIDE_OPEN == b"W\x01\x01R"
    assert rlcs.QD301_OVERRIDE_RELEASE == b"W\x00\x00R"
