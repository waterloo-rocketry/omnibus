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
        # start server
        ctx = mp.get_context('spawn')  # threadsafe multiprocess method
        p = ctx.Process(target=server.server)
        p.start()
        OmnibusCommunicator.server_ip = "127.0.0.1"  # skip discovery

        # wait until the server is alive
        s = Sender()
        r = Receiver("_ALIVE")
        while r.recv(1) is None:
            s.send("_ALIVE", "_ALIVE")

        yield

        # stop the server
        p.terminate()
        p.join()

    @pytest.fixture()
    def sender(self):
        return Sender  # for consistency with receiver

    @pytest.fixture()
    def receiver(self):
        def _receiver(*channel):
            r = Receiver(*channel)
            time.sleep(0.05)  # let the receiver connect to the server so messages aren't dropped
            return r
        return _receiver

    def test_nominal(self, sender, receiver):
        s = sender()
        r = receiver("CHAN")
        s.send("CHAN", "A")
        assert r.recv(10) == "A"

    def test_channels(self, sender, receiver):
        s1 = sender()
        r1 = receiver("CHAN1")
        s2 = sender()
        r2 = receiver("CHAN2")
        r3 = receiver("CHAN")
        s1.send("CHAN1", "A")
        assert r1.recv(10) == "A"
        assert r3.recv(10) == "A"
        assert r2.recv(10) is None
        s2.send("CHAN2", "B")
        assert r2.recv(10) == "B"
        assert r3.recv(10) == "B"
        assert r1.recv(10) is None

    def test_msg_objects(self, sender, receiver):
        s = sender()
        r = receiver("CHAN")
        s.send_message(Message("CHAN", 10, "PAYLOAD"))
        m = r.recv_message(10)
        assert m.channel == "CHAN"
        assert m.timestamp == 10
        assert m.payload == "PAYLOAD"

    def test_multi_channel_recieving(self, sender, receiver):
        s = sender()
        r = receiver("A", "B", "C")
        s.send("A", "message1")
        assert r.recv(10) == "message1"
        s.send("B", "message2")
        assert r.recv(10) == "message2"
        s.send("C", "message3")
        assert r.recv(10) == "message3"


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
        # respond to the IP prompt if discovery times out
        monkeypatch.setattr(sys, "stdin", io.StringIO("timeout"))
        # make sure the server_ip isn't stored from previous tests
        OmnibusCommunicator.server_ip = None

        c = OmnibusCommunicator()
        assert c.server_ip == server.get_ip()

    def test_timeout(self, monkeypatch):
        # respond to the IP prompt if discovery times out
        monkeypatch.setattr(sys, "stdin", io.StringIO("timeout"))
        # make sure the server_ip isn't stored from previous tests
        OmnibusCommunicator.server_ip = None

        c = OmnibusCommunicator()
        assert c.server_ip == "timeout"
