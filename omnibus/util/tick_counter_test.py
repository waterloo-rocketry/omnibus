import pytest
import time

from tick_counter import TickCounter


class TestTickCounter():
    @pytest.fixture()
    def test_instantaneous(self):
        t = TickCounter(2)
        t.tick()
        time.sleep(1)
        t.tick()
        assert(round(t.tick_rate()) == 1)
        assert(t.tick_count() == 2)

    @pytest.fixture()
    def test_running_avg(self):
        t = TickCounter(5)
        for _ in range(5):
            t.tick()
            time.sleep(0.2)
        assert(round(t.tick_rate()) == 5)
        assert(t.tick_count() == 5)
