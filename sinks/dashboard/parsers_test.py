import pytest

from parsers import daq_parser
from parsers import can_parser


class TestParser:
    def test_daq_parser(self):
        data = {
            "timestamp": 4,
            "data": {
                "fake0": [0, 0, 0, 0, 0, 0, 0, 0],
                "fake1": [1, 1, 1, 1, 1],
                "fake2": [2, 2, 2]
            }
        }

        assert daq_parser(data) == [("DAQ|fake0", 4, 0), ("DAQ|fake1", 4, 1), ("DAQ|fake2", 4, 2)]

    def test_can_parser(self):
        can_message = {
            "data": {
                "time": 4
            }
        }

        assert can_parser(can_message) == [("CAN", 4, {"data": {"time": 4}})]
