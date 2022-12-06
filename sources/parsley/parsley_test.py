import struct

import pytest

import parsley
import message_types as mt


class TestParsley:
    @pytest.fixture
    def timestamp(self):
        def _timestamp(val=0):
            return struct.pack(">I", val << 8)[:-1]
        return _timestamp

    def test_parse_timestamp(self, timestamp):
        msg_data = timestamp(12345)
        assert parsley._parse_timestamp(msg_data) == 12345

    def test_gen_cmd(self, timestamp):
        msg_data = timestamp(12345)
        msg_data += struct.pack(">b", mt.gen_cmd_hex["BUS_DOWN_WARNING"])
        res = parsley.parse_gen_cmd(msg_data)
        assert res["time"] == 12345
        assert res["command"] == "BUS_DOWN_WARNING"

    def test_actuator_cmd(self, timestamp):
        msg_data = timestamp()
        msg_data += struct.pack(">b", mt.actuator_id_hex["VENT_VALVE"])
        msg_data += struct.pack(">b", mt.actuator_states_hex["ACTUATOR_CLOSED"])
        res = parsley.parse_actuator_cmd(msg_data)
        assert res["actuator"] == "VENT_VALVE"
        assert res["req_state"] == "ACTUATOR_CLOSED"

    def test_actuator_status(self, timestamp):
        msg_data = timestamp()
        msg_data += struct.pack(">b", mt.actuator_id_hex["INJECTOR_VALVE"])
        msg_data += struct.pack(">bb",
                                mt.actuator_states_hex["ACTUATOR_UNK"], mt.actuator_states_hex["ACTUATOR_CLOSED"])
        res = parsley.parse_actuator_status(msg_data)
        assert res["actuator"] == "INJECTOR_VALVE"
        assert res["req_state"] == "ACTUATOR_CLOSED"
        assert res["cur_state"] == "ACTUATOR_UNK"

    def test_arm_cmd(self, timestamp):
        msg_data = timestamp() + b'\x17'
        res = parsley.parse_arm_cmd(msg_data)
        assert res["altimeter"] == 7
        assert res["state"] == "ARMED"

    def test_arm_status(self, timestamp):
        msg_data = timestamp() + struct.pack(">bHH", 0x04, 12345, 54321)
        res = parsley.parse_arm_status(msg_data)
        assert res["altimeter"] == 4
        assert res["state"] == "DISARMED"
        assert res["drogue_v"] == 12345
        assert res["main_v"] == 54321

    def test_debug_msg(self, timestamp):
        msg_data = timestamp() + b'\x61\x23' + b'ABC'
        res = parsley.parse_debug_msg(msg_data)
        assert res["level"] == 6
        assert res["line"] == 0x123
        assert res["data"] == b'ABC'

    def test_debug_printf(self):
        msg_data = b'ABCDEFGH'
        res = parsley.parse_debug_printf(msg_data)
        assert res["string"] == "ABCDEFGH"

    def test_board_status_nominal(self, timestamp):
        msg_data = timestamp()
        msg_data += struct.pack(">b", mt.board_stat_hex["E_NOMINAL"])
        res = parsley.parse_board_status(msg_data)
        assert res["status"] == "E_NOMINAL"

    def test_board_status_current(self, timestamp):
        msg_data = timestamp()
        msg_data += struct.pack(">bH", mt.board_stat_hex["E_BUS_OVER_CURRENT"], 12345)
        res = parsley.parse_board_status(msg_data)
        assert res["status"] == "E_BUS_OVER_CURRENT"
        assert res["current"] == 12345

    def test_board_status_voltage(self, timestamp):
        msg_data = timestamp()
        msg_data += struct.pack(">bH", mt.board_stat_hex["E_BUS_OVER_VOLTAGE"], 12345)
        res = parsley.parse_board_status(msg_data)
        assert res["status"] == "E_BUS_OVER_VOLTAGE"
        assert res["voltage"] == 12345

    def test_board_status_dead(self, timestamp):
        msg_data = timestamp()
        msg_data += struct.pack(">bb",
                                mt.board_stat_hex["E_BOARD_FEARED_DEAD"], mt.board_id_hex["RADIO"])
        res = parsley.parse_board_status(msg_data)
        assert res["status"] == "E_BOARD_FEARED_DEAD"
        assert res["board_id"] == "RADIO"

    def test_board_status_quiet(self, timestamp):
        msg_data = timestamp()
        msg_data += struct.pack(">bH", mt.board_stat_hex["E_NO_CAN_TRAFFIC"], 12345)
        res = parsley.parse_board_status(msg_data)
        assert res["status"] == "E_NO_CAN_TRAFFIC"
        assert res["err_time"] == 12345

    def test_board_status_sensor(self, timestamp):
        msg_data = timestamp()
        msg_data += struct.pack(">bb",
                                mt.board_stat_hex["E_SENSOR"], mt.sensor_id_hex["SENSOR_BARO"])
        res = parsley.parse_board_status(msg_data)
        assert res["status"] == "E_SENSOR"
        assert res["sensor_id"] == "SENSOR_BARO"

    def test_board_status_actuator(self, timestamp):
        msg_data = timestamp()
        msg_data += struct.pack(">bbb", mt.board_stat_hex["E_ACTUATOR_STATE"],
                                mt.actuator_states_hex["ACTUATOR_CLOSED"], mt.actuator_states_hex["ACTUATOR_UNK"])
        res = parsley.parse_board_status(msg_data)
        assert res["status"] == "E_ACTUATOR_STATE"
        assert res["req_state"] == "ACTUATOR_CLOSED"
        assert res["cur_state"] == "ACTUATOR_UNK"

    def test_sensor_analog(self):
        msg_data = struct.pack(">HbH", 12345, mt.sensor_id_hex["SENSOR_BARO"], 54321)
        res = parsley.parse_sensor_analog(msg_data)
        assert res["time"] == 12345
        assert res["sensor_id"] == "SENSOR_BARO"
        assert res["value"] == 54321

    def test_sensor_altitude(self, timestamp):
        msg_data = timestamp() + struct.pack(">i", -12345)
        res = parsley.parse_sensor_altitude(msg_data)
        assert res["altitude"] == -12345

    def test_sensor_temp(self, timestamp):
        msg_data = timestamp() + b'\x12'
        msg_data += struct.pack(">I", int(12.5 * 2**10))[1:]
        res = parsley.parse_sensor_temp(msg_data)
        assert res["sensor_id"] == 0x12
        assert res["temperature"] == 12.5

    def test_gps_timestamp(self, timestamp):
        msg_data = timestamp() + struct.pack(">bbbb", 12, 23, 34, 45)
        res = parsley.parse_gps_timestamp(msg_data)
        assert res["hrs"] == 12
        assert res["mins"] == 23
        assert res["secs"] == 34
        assert res["dsecs"] == 45

    def test_gps_latitude(self, timestamp):
        msg_data = timestamp() + struct.pack(">bbHc", 12, 23, 12345, b'N')
        res = parsley.parse_gps_latitude(msg_data)
        assert res["degs"] == 12
        assert res["mins"] == 23
        assert res["dmins"] == 12345
        assert res["direction"] == "N"

    def test_gps_longitude(self, timestamp):
        msg_data = timestamp() + struct.pack(">bbHc", 12, 23, 12345, b'W')
        res = parsley.parse_gps_longitude(msg_data)
        assert res["degs"] == 12
        assert res["mins"] == 23
        assert res["dmins"] == 12345
        assert res["direction"] == "W"

    def test_gps_altitude(self, timestamp):
        msg_data = timestamp() + struct.pack(">Hbc", 12345, 12, b'm')
        res = parsley.parse_gps_altitude(msg_data)
        assert res["altitude"] == 12345
        assert res["daltitude"] == 12
        assert res["unit"] == "m"

    def test_gps_info(self, timestamp):
        msg_data = timestamp() + struct.pack(">bb", 12, 23)
        res = parsley.parse_gps_info(msg_data)
        assert res["num_sats"] == 12
        assert res["quality"] == 23

    def test_fill_lvl(self, timestamp):
        msg_data = timestamp()
        msg_data += struct.pack(">bb", 9, mt.fill_direction_hex["FILLING"])
        res = parsley.parse_fill_lvl(msg_data)
        assert res["level"] == 9
        assert res["direction"] == "FILLING"

    def test_parse(self, monkeypatch):
        def parse_monkey(msg_data):
            return {"monkey": msg_data}
        monkeypatch.setitem(parsley._func_map, "LEDS_ON", parse_monkey)

        msg_sid = mt.msg_type_hex["LEDS_ON"] | mt.board_id_hex["ARMING"]
        msg_data = [1, 2, 3, 4]
        res = parsley.parse(msg_sid, msg_data)
        assert res["msg_type"] == "LEDS_ON"
        assert res["board_id"] == "ARMING"
        assert res["data"]["monkey"] == msg_data

    def test_parse_usb(self):
        msg_sid, msg_data = parsley.parse_usb_debug("$555:1,2,FF")
        assert msg_sid == 0x555
        assert msg_data == [1, 2, 0xFF]

    def test_parse_logger(self):
        msg_sid, msg_data = parsley.parse_logger("5550102FF")
        assert msg_sid == 0x555
        assert msg_data == [1, 2, 0xFF]

    def test_reset_cmd(self, timestamp):
        msg_data = timestamp() + struct.pack(">b", 3)
        res = parsley.parse_reset_cmd(msg_data)
        assert res["board_id"] == "LOGGER"

        msg_data = timestamp() + struct.pack(">b", 0)
        res = parsley.parse_reset_cmd(msg_data)
        assert res["board_id"] == "ALL"

    def test_debug_radio_cmd(self):
        msg_data = b'RADIO'
        res = parsley.parse_debug_radio_cmd(msg_data)
        assert res["string"] == "RADIO"

    def test_sensor_acc(self):
        msg_data = struct.pack(">Hhhh", 12345, 1, 2, 3)
        res = parsley.parse_sensor_acc_gyro_mag(msg_data)
        assert res["time"] == 12345
        assert res["x"] == 1
        assert res["y"] == 2
        assert res["z"] == 3

        msg_data = struct.pack(">Hhhh", 12345, -1, -2, -3)
        res = parsley.parse_sensor_acc_gyro_mag(msg_data)
        assert res["time"] == 12345
        assert res["x"] == -1
        assert res["y"] == -2
        assert res["z"] == -3

    def test_sensor_gyro(self, timestamp):
        # covered by test_sensor_acc
        pass

    def test_sensor_mag(self, timestamp):
        # covered by test_sensor_acc
        pass

    def test_radi_value(self, timestamp):
        msg_data = timestamp() + struct.pack(">bH", 1, 500)
        res = parsley.parse_radi_value(msg_data)
        assert res["radi_board"] == 1
        assert res["radi"] == 500

    def test_leds_on(self):
        # LED_ON message has no message body
        pass

    def test_leds_off(self):
        # LED_OFF message has no message body
        pass
