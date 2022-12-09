import pytest

import config
from publisher import Publisher


class TestPublisher:
    def test_subscribe(self):
        p = Publisher()
        assert len(p.streams) == 0

        p.subscribe("test1", True)
        assert p.streams["test1"] == [True]

        p.subscribe("test2", False)
        assert p.streams["test2"] == [False]
        assert p.streams["test1"] == [True]

        p.subscribe("test1", False)
        assert p.streams["test1"] == [True, False]

    def test_unsubscribe_from_all(self):
        p = Publisher()
        p.subscribe("test1", True)
        p.subscribe("test2", True)
        assert p.streams["test1"] == [True]
        assert p.streams["test2"] == [True]

        p.unsubscribe_from_all(True)
        assert p.streams["test1"] == []
        assert p.streams["test2"] == []

        p.subscribe("test1", True)
        p.subscribe("test2", False)
        assert p.streams["test1"] == [True]
        assert p.streams["test2"] == [False]

        p.unsubscribe_from_all(True)
        assert p.streams["test1"] == []
        assert p.streams["test2"] == [False]

    def test_update(self):
        p = Publisher()
        data = [0]

        def mutate_counter(payload):
            data[0] = payload

        p.subscribe("test1", mutate_counter)
        assert data == [0]
        p.update("test1", 2)
        assert data == [2]

        p.update("test2", 3)
        assert len(p.streams) == 2
        assert data == [2]

        p.unsubscribe_from_all(mutate_counter)
        p.update("test1", 3)
        assert data == [2]
