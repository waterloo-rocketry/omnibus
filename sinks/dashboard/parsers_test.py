import pytest
from typing import List, Tuple, Union, Any

from parsers import daq_parser
from parsers import can_parser


class TestParser:
    def test_daq_parser(self):
        data: dict[str, Union[int, dict[str, List[int]]]] = {
            "timestamp": 4,
            "data": {
                "fake0": [0, 0, 0, 0, 0, 0, 0, 0],
                "fake1": [1, 1, 1, 1, 1],
                "fake2": [2, 2, 2]
            }
        }

        assert daq_parser(data) == [("fake0", 4, 0), ("fake1", 4, 1), ("fake2", 4, 2)]

    def test_can_parser(self):
        can_message: dict[str, Union[str, str, dict[str, Union[float, str, int]]]] = {
            'board_id': 'CHARGING',
            'msg_type': 'SENSOR_ANALOG',
            'data': {
                'time': 37.595,
                'sensor_id': 'SENSOR_GROUND_VOLT',
                'value': 13104
            }
        }

        assert can_parser(can_message) == [
            ("CHARGING/SENSOR_ANALOG/SENSOR_GROUND_VOLT/value", 37.595, 13104)]
