import io
import multiprocessing as mp
import sys
import time

import pytest

from omnibus import Sender, Receiver, Message, server
from omnibus.omnibus import OmnibusCommunicator

class TestOmnibus:
    @pytest.fixture(autouse=True, scope="class")
    def server(self):
        ctx = mp.get_context('spawn')
        p = ctx.Process(target=server.server)
        p.start()
        OmnibusCommunicator.server_ip = "127.0.0.1"

        s = Sender("_ALIVE")
        r = Receiver("_ALIVE")
        while r.recv(1) is None:
            s.send("_ALIVE")

        yield

        p.terminate()
        p.join()

    @pytest.fixture()
    def sender(self):
        return Sender

    @pytest.fixture()
    def receiver(self):
        def _receiver(channel):
            r = Receiver(channel)
            time.sleep(0.05)
            return r
        return _receiver

    def test_nominal(self, sender, receiver):
        s = sender("CHAN")
        r = receiver("CHAN")
        s.send(1)
        assert r.recv(1) == 1

    def test_channels(self, sender, receiver):
        s1 = sender("CHAN1")
        r1 = receiver("CHAN1")
        s2 = sender("CHAN2")
        r2 = receiver("CHAN2")
        r3 = receiver("CHAN")
        s1.send(1)
        assert r1.recv(1) == 1
        assert r3.recv(1) == 1
        assert r2.recv(1) is None
        s2.send(2)
        assert r2.recv(1) == 2
        assert r3.recv(1) == 2
        assert r1.recv(1) is None

    def test_msg_objects(self, sender, receiver):
        s = sender("")
        r = receiver("")
        s.send_message(Message("CHAN", 10, "HI"))
        m = r.recv_message(1)
        assert m.channel == "CHAN"
        assert m.timestamp == 10
        assert m.payload == "HI"

class TestIPBroadcast:
    @pytest.fixture()
    def broadcaster(self):
        ctx = mp.get_context('spawn')
        p = ctx.Process(target=server.ip_broadcast)
        p.start()
        yield
        p.terminate()
        p.join()

    def test_broadcast(self, broadcaster, monkeypatch):
        monkeypatch.setattr(sys, "stdin", io.StringIO("timeout"))
        OmnibusCommunicator.server_ip = None
        c = OmnibusCommunicator()
        assert c.server_ip == server.get_ip()

    def test_timeout(self, monkeypatch):
        monkeypatch.setattr(sys, "stdin", io.StringIO("timeout"))
        OmnibusCommunicator.server_ip = None
        c = OmnibusCommunicator()
        assert c.server_ip == "timeout"
