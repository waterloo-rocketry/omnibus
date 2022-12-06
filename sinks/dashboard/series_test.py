import pytest

import config
from series import Series


class TestSeries:
    @pytest.fixture(autouse=True)  # runs before every unit test
    def constants(self, monkeypatch):
        monkeypatch.setattr(config, "GRAPH_RESOLUTION", 10)
        monkeypatch.setattr(config, "GRAPH_DURATION", 10)

    def test_no_downsample(self):
        s = Series("NAME")
        s.add([1/10, 1])
        assert s.points[-2] == 1  # make sure we back-fill()ed the array
        assert s.points[-1] == 1
        s.add([2/10, 2])
        assert s.points[-3] == 1
        assert s.points[-2] == 1
        assert s.points[-1] == 2

    def test_downsample(self):
        s = Series("NAME")
        s.add([1/20, 1])  # downsampled away
        s.add([2/20, 2])
        assert s.points[-2] == 2
        assert s.points[-1] == 2
        s.add([3/20, 3])  # downsampled away
        assert s.points[-2] == 2
        assert s.points[-1] == 2
        s.add([4/20, 4])
        assert s.points[-3] == 2
        assert s.points[-2] == 2
        assert s.points[-1] == 4
