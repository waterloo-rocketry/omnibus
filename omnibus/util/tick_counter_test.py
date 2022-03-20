from cgi import test
from itertools import tee
from re import T
import pytest
import time

from tick_counter import TickCounter


class TickCounterTest:
    @pytest.fixture(autouse=True)  # runs before every unit test
    def test_instantaneous(self):
        t = TickCounter()
        t.tick()
        time.sleep(1)
        t.tick()
        assert(int(t.tick_rate()) == 1)
        assert(t.tick_count() == 2)

    def test_running_avg(self):
        t = TickCounter()
        for i in range(5):
            t.tick()
            t.sleep(0.2)
        assert(int(t.tick_rate()*5) == 1)
        assert(t.tick_count() == 5)
