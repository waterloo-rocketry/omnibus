import pytest

import parsers


class TestDAQParser:
    @pytest.fixture
    def parser(self):
        return parsers.DAQParser("CHANNEL", "SENSOR")

    def test_nominal(self, parser):
        payload = {
            "timestamp": 10,
            "data": {"NOTSENSOR": [1, 2, 3], "SENSOR": [4, 5, 6]}
        }
        time, data = parser.parse(payload)
        assert time == 0  # uses first timestamp recieved as zero
        assert data == 4

    def test_no_data(self, parser):
        payload = {
            "timestamp": 10,
            "data": {"NOTSENSOR": [1, 2, 3]}
        }
        assert parser.parse(payload) is None

    def test_time_offset(self, parser):
        payload = {
            "timestamp": 10,
            "data": {"SENSOR": [4, 5, 6]}
        }
        parser.parse(payload)
        payload["timestamp"] = 20
        time, _ = parser.parse(payload)
        assert time == 10  # uses first timestamp recieved as zero


class TestParsleyParser:
    @pytest.fixture
    def parser(self):
        return parsers.ParsleyParser("CHANNEL", "MSG_TYPE", "KEY")

    def test_nominal(self, parser):
        payload = {
            "msg_type": "MSG_TYPE",
            "board_id": "BOARD_ID",
            "data": {"time": 10000, "KEY": "VALUE"}
        }
        t, v = parser.parse(payload)
        assert t == 10
        assert v == "VALUE"

    def test_msg_type(self, parser):
        payload = {
            "msg_type": "NOT_MSG_TYPE",
            "board_id": "BOARD_ID",
            "data": {"time": 10000, "KEY": "VALUE"}
        }
        assert parser.parse(payload) is None

    def test_filter(self, parser):
        parser.filter = lambda payload: "IGNORE" not in payload["data"]
        payload = {
            "msg_type": "MSG_TYPE",
            "board_id": "BOARD_ID",
            "data": {"time": 10000, "KEY": "VALUE", "IGNORE": "ME"}
        }
        assert parser.parse(payload) is None

    def test_time(self, parser):
        payload = {
            "msg_type": "MSG_TYPE",
            "board_id": "BOARD_ID",
            "data": {"time": 1000, "KEY": "VALUE"}
        }
        parser.parse(payload)
        payload["data"]["time"] = 0
        assert parser.parse(payload)[0] == 1
        payload["data"]["time"] = 2000
        assert parser.parse(payload)[0] == 3


class TestFillSensingParser:
    @pytest.fixture
    def parser(self):
        return parsers.FillSensingParser("CHANNEL")

    def test_nominal(self, parser):
        payload = {
            "msg_type": "FILL_LVL",
            "data": {"time": 1000, "level": 3}
        }
        t, v = parser.parse(payload)
        assert t == 1
        assert v == 3


class TestTemperatureParser:
    @pytest.fixture
    def parser(self):
        return parsers.TemperatureParser("CHANNEL", "SENSOR")

    def test_nominal(self, parser):
        payload = {
            "msg_type": "SENSOR_TEMP",
            "data": {"time": 1000, "temperature": 3, "sensor_id": "SENSOR"}
        }
        t, v = parser.parse(payload)
        assert t == 1
        assert v == 3

    def test_filter(self, parser):
        payload = {
            "msg_type": "SENSOR_TEMP",
            "data": {"time": 1000, "temperature": 3, "sensor_id": "NOT_SENSOR"}
        }
        assert parser.parse(payload) is None


class TestAccelParser:
    @pytest.fixture
    def parser(self):
        return parsers.AccelParser("CHANNEL", "AXIS")

    def test_nominal(self, parser):
        payload = {
            "msg_type": "SENSOR_ACC",
            "data": {"time": 1000, "AXIS": 3}
        }
        t, v = parser.parse(payload)
        assert t == 1
        assert v == 3


class TestAnalogSensorParser:
    @pytest.fixture
    def parser(self):
        return parsers.AnalogSensorParser("CHANNEL", "SENSOR")

    def test_nominal(self, parser):
        payload = {
            "msg_type": "SENSOR_ANALOG",
            "data": {"time": 1000, "value": 3, "sensor_id": "SENSOR"}
        }
        t, v = parser.parse(payload)
        assert t == 1
        assert v == 3

    def test_filter(self, parser):
        payload = {
            "msg_type": "SENSOR_ANALOG",
            "data": {"time": 1000, "value": 3, "sensor_id": "NOT_SENSOR"}
        }
        assert parser.parse(payload) is None
