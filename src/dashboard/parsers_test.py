import pytest

from parsers import daq_parser
from parsers import can_parser

@pytest.fixture(autouse=True)
def _reset_parser_state():
    import parsers
    parsers.last_timestamp.clear()
    parsers.offset_timestamp.clear()

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

    def test_can_parser_sensor_analog32(self):
        can_message = {
            'board_type_id': 'INJECTOR',
            'board_inst_id': 'ROCKET',
            'msg_prio': 'HIGH',
            'msg_type': 'SENSOR_ANALOG32',
            'msg_metadata': 'SENSOR_PT_CHANNEL_1',
            'data': {'time': 37.595, 'value': 1310},
        }

        assert can_parser(can_message) == [
            ("INJECTOR/ROCKET/SENSOR_ANALOG32/SENSOR_PT_CHANNEL_1/value", 37.595, 1310)]

    def test_can_parser_sensor_analog16(self):
        can_message = {
            'board_type_id': 'TELEMETRY',
            'board_inst_id': 'ROCKET',
            'msg_prio': 'LOW',
            'msg_type': 'SENSOR_ANALOG16',
            'msg_metadata': 'SENSOR_BATT_VOLT',
            'data': {'time': 10.0, 'value': 3300},
        }

        assert can_parser(can_message) == [
            ("TELEMETRY/ROCKET/SENSOR_ANALOG16/SENSOR_BATT_VOLT/value", 10.0, 3300)]

    def test_can_parser_sensor_2d_analog24(self):
        can_message = {
            'board_type_id': 'CANARD', 'board_inst_id': 'ROCKET',
            'msg_prio': 'LOW', 'msg_type': 'SENSOR_2D_ANALOG24',
            'msg_metadata': 'SENSOR_MAG',
            'data': {'time': 50.0, 'value_x': 11, 'value_y': 22},
        }
        assert can_parser(can_message) == [
            ("CANARD/ROCKET/SENSOR_2D_ANALOG24/SENSOR_MAG/value_x", 50.0, 11),
            ("CANARD/ROCKET/SENSOR_2D_ANALOG24/SENSOR_MAG/value_y", 50.0, 22),
        ]

    def test_can_parser_sensor_3d_analog16(self):
        can_message = {
            'board_type_id': 'CANARD', 'board_inst_id': 'ROCKET',
            'msg_prio': 'LOW', 'msg_type': 'SENSOR_3D_ANALOG16',
            'msg_metadata': 'SENSOR_IMU_ACCEL',
            'data': {'time': 60.0, 'value_x': 1, 'value_y': 2, 'value_z': 3},
        }
        assert can_parser(can_message) == [
            ("CANARD/ROCKET/SENSOR_3D_ANALOG16/SENSOR_IMU_ACCEL/value_x", 60.0, 1),
            ("CANARD/ROCKET/SENSOR_3D_ANALOG16/SENSOR_IMU_ACCEL/value_y", 60.0, 2),
            ("CANARD/ROCKET/SENSOR_3D_ANALOG16/SENSOR_IMU_ACCEL/value_z", 60.0, 3),
        ]

    def test_can_parser_general_board_status_nominal(self):
        can_message = {
            'board_type_id': 'POWER', 'board_inst_id': 'ROCKET',
            'msg_prio': 'LOW', 'msg_type': 'GENERAL_BOARD_STATUS',
            'msg_metadata': 0,
            'data': {'time': 100.0, 'board_error_bitfield': 'E_NOMINAL'},
        }
        result = can_parser(can_message)
        err_topics = [r for r in result if r[0] == "POWER/ROCKET/ERROR"]
        assert err_topics == []
        assert ("POWER/ROCKET/GENERAL_BOARD_STATUS/0/board_error_bitfield", 100.0, 'E_NOMINAL') == result[0]

    def test_can_parser_general_board_status_error(self):
        can_message = {
            'board_type_id': 'GPS', 'board_inst_id': 'ROCKET',
            'msg_prio': 'LOW', 'msg_type': 'GENERAL_BOARD_STATUS',
            'msg_metadata': 0,
            'data': {'time': 110.0, 'board_error_bitfield': 'E_GPS_FIX_LOST'},
        }
        result = can_parser(can_message)
        err_topics = [r for r in result if r[0] == "GPS/ROCKET/ERROR"]
        assert len(err_topics) == 1
        assert err_topics[0][2] == 'E_GPS_FIX_LOST'
