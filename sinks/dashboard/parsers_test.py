from collections import defaultdict

import pytest

import parsers


class MockSeries:
    def __init__(self):
        self.data = []

    def add(self, time, point):
        self.data.append((time, point))


class TestDAQParser:
    @pytest.fixture
    def parser(self):
        p = parsers.DAQParser()
        p.series = defaultdict(MockSeries)
        return p

    def test_nominal():
        payload = {
            "timestamp": 0,
            # [1, 2, 6] to make sure its not just returning the middle element
            "data": {"SENSOR 1": [1, 2, 6], "SENSOR 2": [4, 5, 6]}
        }
        parsers.parse("DAQ", payload)
        # values should be averagd
        #assert parser.series.get("SENSOR 1").data == [(0, 3)]
        #assert parser.series.get("SENSOR 2").data == [(0, 5)]

    def test_multiple(self, parser):
        payload = {
            "timestamp": 00,
            "data": {"SENSOR": [1]}
        }
        parser.parse(payload)
        payload["timestamp"] = 10
        parser.parse(payload)
        assert parser.series.get("SENSOR").data == [(0, 1), (10, 1)]

    def test_time_offset(self, parser):
        payload = {
            "timestamp": 10,
            "data": {"SENSOR": [4]}
        }
        parser.parse(payload)
        payload["timestamp"] = 20
        parser.parse(payload)
        # uses first timestamp recieved as zero
        assert parser.series.get("SENSOR").data == [(0, 4), (10, 4)]


class TestParsleyParser:
    @pytest.fixture
    def parser(self):
        data = []
        p = parsers.ParsleyParser("MSG_TYPE")
        # mock out parser.parse_can to just append to data
        # mutability is an easy way to override functionality here without needing a subclass
        p.parse_can = data.append
        return p, data

    def test_nominal(self, parser):
        parser, data = parser
        payload = {
            "msg_type": "MSG_TYPE",
            "board_id": "BOARD_ID",
            "data": {"time": 10000, "KEY": "VALUE"}
        }
        parser.parse(payload)
        assert data[0]["data"]["time"] == 10

    def test_msg_type(self, parser):
        parser, data = parser
        payload = {
            "msg_type": "NOT_MSG_TYPE",
            "board_id": "BOARD_ID",
            "data": {"time": 10000, "KEY": "VALUE"}
        }
        parser.parse(payload)
        assert data == []

    def test_time(self, parser):
        parser, data = parser
        payload = {
            "msg_type": "MSG_TYPE",
            "board_id": "BOARD_ID",
            "data": {"time": 1000, "KEY": "VALUE"}
        }
        parser.parse(payload)
        assert data[-1]["data"]["time"] == 1
        payload["data"]["time"] = 0
        parser.parse(payload)
        assert data[-1]["data"]["time"] == 1
        payload["data"]["time"] = 2000
        parser.parse(payload)
        assert data[-1]["data"]["time"] == 3


class TestFillSensingParser:
    @pytest.fixture
    def parser(self):
        p = parsers.FillSensingParser()
        p.series = defaultdict(MockSeries)
        return p

    def test_nominal(self, parser):
        payload = {
            "msg_type": "FILL_LVL",
            "data": {"time": 1000, "level": 3}
        }
        parser.parse(payload)
        assert parser.series.get("Fill Level").data == [(1, 3)]


class TestTemperatureParser:
    @pytest.fixture
    def parser(self):
        p = parsers.TemperatureParser()
        p.series = defaultdict(MockSeries)
        return p

    def test_nominal(self, parser):
        payload = {
            "msg_type": "SENSOR_TEMP",
            "data": {"time": 1000, "temperature": 3, "sensor_id": "SENSOR"}
        }
        parser.parse(payload)
        assert parser.series.get("Temperature SENSOR").data == [(1, 3)]


class TestAccelParser:
    @pytest.fixture
    def parser(self):
        p = parsers.AccelParser()
        p.series = defaultdict(MockSeries)
        return p

    def test_nominal(self, parser):
        payload = {
            "msg_type": "SENSOR_ACC",
            "data": {"time": 1000, "x": 1, "y": 2, "z": 3}
        }
        parser.parse(payload)
        assert parser.series.get("Acceleration (x)").data == [(1, 1)]
        assert parser.series.get("Acceleration (y)").data == [(1, 2)]
        assert parser.series.get("Acceleration (z)").data == [(1, 3)]


class TestAnalogSensorParser:
    @pytest.fixture
    def parser(self):
        p = parsers.AnalogSensorParser()
        p.series = defaultdict(MockSeries)
        return p

    def test_nominal(self, parser):
        payload = {
            "msg_type": "SENSOR_ANALOG",
            "data": {"time": 1000, "value": 3, "sensor_id": "SENSOR"}
        }
        parser.parse(payload)
        assert parser.series.get("CAN Sensor SENSOR").data == [(1, 3)]
