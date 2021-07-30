import pytest

from parsers import DAQParser, TemperatureParser, FillSensingParser

class TestDAQParser:
    @pytest.fixture
    def parser(self):
        return DAQParser("CHANNEL", "SENSOR")

    def test_nominal(self, parser):
        payload = {
            "timestamp": 10,
            "data": {"NOTSENSOR": [1, 2, 3], "SENSOR": [4, 5, 6]}
        }
        time, data = parser.parse(payload)
        assert time == 0 # uses first timestamp recieved as zero
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
        assert time == 10 # uses first timestamp recieved as zero

class TestFillSensingParser:
    @pytest.fixture
    def parser(self):
        return FillSensingParser("CHANNEL")

    def test_nominal(self, parser):
        payload = "[ FILL_LVL                  FILL       ] t=      123ms  LEVEL=4             DIRECTION=FILLING"
        time, data = parser.parse(payload)
        assert time == 0.123
        assert data == 4

    def test_other_message(self, parser):
        payload = "[ SENSOR_TEMP               TEMP_SENSE ] t=      123ms  SENSOR=4            TEMP=56.789"
        assert parser.parse(payload) is None

class TestTemperatureParser:
    @pytest.fixture
    def parser(self):
        return TemperatureParser("CHANNEL", 0)

    def test_nominal(self, parser):
        payload = "[ SENSOR_TEMP               TEMP_SENSE ] t=      123ms  SENSOR=0            TEMP=56.789"
        time, data = parser.parse(payload)
        assert time == 0.123
        assert data == 56.789

    def test_other_sensor(self, parser):
        payload = "[ SENSOR_TEMP               TEMP_SENSE ] t=      123ms  SENSOR=10           TEMP=56.789"
        assert parser.parse(payload) is None

    def test_other_message(self, parser):
        payload = "[ FILL_LVL                  FILL       ] t=      123ms  LEVEL=4             DIRECTION=FILLING"
        assert parser.parse(payload) is None
