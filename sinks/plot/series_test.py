import pytest

import config
from series import Series
from parsers import Parser

class MockParser(Parser):
    def parse(self, payload):
        return payload, payload # use payload as timestamp too

class TestSeries:
    @pytest.fixture(autouse=True) # runs before every unit test
    def constants(self, monkeypatch):
        monkeypatch.setattr(config, "GRAPH_RESOLUTION", 10)
        monkeypatch.setattr(config, "GRAPH_DURATION", 10)

    @pytest.fixture(autouse=True) # runs before every unit test
    def series_cleanup(self):
        yield
        Series.series = []

    def test_no_downsample(self):
        s = Series("NAME", 5, MockParser(""))
        assert s.downsample == 1
        assert len(s.times) == len(s.points) == 5*10
        s.add(1)
        assert s.points[-2] == 1 # make sure we back-fill()ed the array
        assert s.points[-1] == 1
        s.add(2)
        assert s.points[-3] == 1
        assert s.points[-2] == 1
        assert s.points[-1] == 2

    def test_downsample(self):
        s = Series("NAME", 20, MockParser(""))
        assert s.downsample == 2
        assert len(s.times) == len(s.points) == 10*10
        s.add(1) # downsampled away
        s.add(2)
        assert s.points[-2] == 2
        assert s.points[-1] == 2
        s.add(3) # downsampled away
        assert s.points[-2] == 2
        assert s.points[-1] == 2
        s.add(4)
        assert s.points[-3] == 2
        assert s.points[-2] == 2
        assert s.points[-1] == 4

    def test_parse(self):
        a = Series("A", 5, MockParser("A"))
        aa = Series("AA", 5, MockParser("A"))
        b = Series("B", 5, MockParser("B"))
        Series.parse("A", 1)
        Series.parse("B", 2)
        assert a.points[-2] == 1
        assert a.points[-2] == 1
        assert aa.points[-1] == 1
        assert aa.points[-1] == 1
        assert b.points[-2] == 2
        assert b.points[-1] == 2
