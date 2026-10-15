import pytest
import time
from typing import Callable, cast

from .tick_counter import TickCounter

approx = cast("Callable[[float], object]", pytest.approx)


class TestTickCounter:
    def test_nominal(self) -> None:
        t = TickCounter(0.4)
        for _ in range(3):
            time.sleep(0.1)
            t.tick()
        assert t.tick_rate() == approx(3 / 0.4)
        assert t.tick_count() == 3

    def test_expire(self) -> None:
        t = TickCounter(0.15)
        for _ in range(4):
            time.sleep(0.1)
            t.tick()
        assert t.tick_rate() == approx(2 / 0.15)
        time.sleep(0.1)
        assert t.tick_rate() == approx(1 / 0.15)
