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

        assert daq_parser(data) == [("fake0", 4, 0), ("fake1", 4, 1), ("fake2", 4, 2)]

    def test_can_parser(self):
        can_message = {
            'board_type_id': 'INJ_SENSOR',
            'board_inst_id': 'GENERIC',
            'msg_prio': 'HIGH',
            'msg_type': 'SENSOR_ANALOG',
            'data': {
                'time': 37.595,
                'sensor_id': 'SENSOR_PRESSURE_OX',
                'value': 1310
            }
        }

        assert can_parser(can_message) == [
            ("INJ_SENSOR/GENERIC/SENSOR_ANALOG/SENSOR_PRESSURE_OX/value", 37.595, 1310)]
