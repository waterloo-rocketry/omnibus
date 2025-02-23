import pytest
import time

from omnibus.util import TickCounter


class TestTickCounter:
    def test_nominal(self):
        t = TickCounter(0.4)
        for _ in range(3):
            time.sleep(0.1)
            t.tick()
        assert t.tick_rate() == pytest.approx(3 / 0.4)
        assert t.tick_count() == 3

    def test_expire(self):
        t = TickCounter(0.15)
        for _ in range(4):
            time.sleep(0.1)
            t.tick()
        assert t.tick_rate() == pytest.approx(2 / 0.15)
        time.sleep(0.1)
        assert t.tick_rate() == pytest.approx(1 / 0.15)
