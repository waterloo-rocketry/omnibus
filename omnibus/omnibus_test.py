import io
import multiprocessing as mp
from multiprocessing.context import SpawnProcess
import sys
import time
from typing import Callable

import pytest

from omnibus import Sender, Receiver, Message, server
from omnibus.omnibus import OmnibusCommunicator


class TestOmnibus:
    @pytest.fixture(autouse=True, scope="class")
    def server(self):
        # start server
        ctx = mp.get_context("spawn")  # threadsafe multiprocess method
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
        def _receiver(*channels):
            r = Receiver(*channels)
            time.sleep(
                0.05
            )  # let the receiver connect to the server so messages aren't dropped
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
        r = receiver("CHAN1", "CHAN2", "CHAN3")
        s.send("CHAN1", "A")
        assert r.recv(10) == "A"
        s.send("CHAN2", "B")
        assert r.recv(10) == "B"
        s.send("CHAN3", "C")
        assert r.recv(10) == "C"


class TestIPBroadcast:
    @pytest.fixture()
    def broadcaster(self):
        ctx = mp.get_context("spawn")
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


class TestNetworkReset:
    @pytest.fixture()
    def start_stop_capable_server(self):
        def __server():
            # start server
            ctx = mp.get_context("spawn")  # threadsafe multiprocess method
            p = ctx.Process(target=server.server)
            p.start()
            OmnibusCommunicator.server_ip = "127.0.0.1"  # skip discovery

            # wait until the server is alive
            s = Sender()
            r = Receiver("_ALIVE")
            while r.recv(1) is None:
                s.send("_ALIVE", "_ALIVE")

            return p  # pass control of the server process to the test

        return __server

    @pytest.fixture()
    def sender(self):
        return Sender  # for consistency with receiver

    @pytest.fixture()
    def receiver(self):
        def _receiver(*channels):
            r = Receiver(*channels, seconds_until_reconnect_attempt=2)
            time.sleep(
                0.05
            )  # let the receiver connect to the server so messages aren't dropped
            return r

        return _receiver

    # Note that these unit tests are not the only validation of this feature
    # End-to-end testing must be done to ensure that this also works when
    # the network environment changes, or the server changes, etc.
    # This is only an assessment of the reset capabilities of the receiver
    def test_receive_message_after_server_restart(
        self,
        start_stop_capable_server: Callable[[], SpawnProcess],
        sender: Callable[[], Sender],
        receiver: Callable[..., Receiver],
    ):
        server_process: SpawnProcess | None = None
        try:
            server_process = start_stop_capable_server()
            source: Sender = sender()
            sink: Receiver = receiver("_TESTING")
            source.send("_TESTING", "PAYLOAD")
            assert sink.recv(10) == "PAYLOAD"
            server_process.terminate()
            server_process.join()
            server_process = None
            server_process = start_stop_capable_server()
            time.sleep(0.5)
            source.send("_TESTING", "PAYLOAD2")
            assert sink.recv(10) == "PAYLOAD2"
        finally:
            if server_process != None:
                server_process.terminate()
                server_process.join()

    # This is NOT a fully accurate test! Assess using real network disconnects as well!
    # We simulate a network change by starting the receiver with a bad server IP
    def test_receive_after_switching_network(
        self,
        start_stop_capable_server: Callable[[], SpawnProcess],
        sender: Callable[[], Sender],
        receiver: Callable[..., Receiver],
    ):
        server_process = None
        try:
            server_process = start_stop_capable_server()
            source: Sender = sender()
            OmnibusCommunicator.server_ip = "1.1.1.1"  # Set to some bad IP
            sink: Receiver = receiver("_TESTING")
            source.send("_TESTING", "PAYLOAD")
            sink.recv(10)
            sink.recv(10)  # Run 2 receives with the bad IP
            OmnibusCommunicator.server_ip = "127.0.0.1"  # Switch back to a good IP
            sink._reset()
            time.sleep(0.05)  # Let it reconnect
            source.send("_TESTING", "PAYLOAD2")
            assert sink.recv(10) == "PAYLOAD2"
        finally:
            if server_process != None:
                server_process.terminate()
                server_process.join()

    def test_autorecover_from_network_switch(
        self,
        start_stop_capable_server: Callable[[], SpawnProcess],
        sender: Callable[[], Sender],
        receiver: Callable[..., Receiver],
    ):
        server_process = None
        try:
            server_process = start_stop_capable_server()
            source: Sender = sender()
            OmnibusCommunicator.server_ip = "1.1.1.1"  # Set to some bad IP
            sink: Receiver = receiver("_TESTING")
            source.send("_TESTING", "PAYLOAD")
            sink.recv(10)
            sink.recv(10)  # Run 2 receives with the bad IP
            OmnibusCommunicator.server_ip = "127.0.0.1"  # Switch back to a good IP
            i = 0
            connection_regained_time = time.time()  # Connection regained
            while i < 600 and sink.recv(1) == None:
                time.sleep(0.025)
                source.send("_TESTING", "_ALIVE")
            receiver_recovered_time = time.time()
            source.send("_TESTING", "PAYLOAD2")
            assert sink.recv(10) == "PAYLOAD2"
            print(
                "Recovery Time: "
                + str(receiver_recovered_time - connection_regained_time)
            )
            assert (
                receiver_recovered_time - connection_regained_time < 2.5
            )  # It should receive a message immediately after first reconnect attempt
        finally:
            if server_process != None:
                server_process.terminate()
                server_process.join()

    def test_missed_msg(
        self,
        start_stop_capable_server: Callable[[], SpawnProcess],
        sender: Callable[[], Sender],
        receiver: Callable[..., Receiver],
    ):
        server_process: SpawnProcess | None = None
        try:
            server_process = start_stop_capable_server()
            source: Sender = sender()
            sink: Receiver = receiver("_TESTING")
            source.send("_TESTING", "PAYLOAD")
            assert sink.recv(10) == "PAYLOAD"
            # Note that any message sent before a reset cannot be received after
            # This is intended behaviour as a reset is only triggered when no
            # message is being received. Therefore, you should never need to
            # respond to a message after a reset.
            a = time.time()
            sink._reset()
            b = time.time()
            print(b - a)
            # The Receiver needs about 0.05 seconds to reconnect
            time.sleep(0.05)
            source.send("_TESTING", "PAYLOAD2")
            assert sink.recv(10) == "PAYLOAD2"
        finally:
            if server_process != None:
                server_process.terminate()
                server_process.join()


class TestTimeouts:
    @pytest.fixture()
    def start_stop_capable_server(self):
        def __server():
            # start server
            ctx = mp.get_context("spawn")  # threadsafe multiprocess method
            p = ctx.Process(target=server.server)
            p.start()
            OmnibusCommunicator.server_ip = "127.0.0.1"  # skip discovery

            # wait until the server is alive
            s = Sender()
            r = Receiver("_ALIVE")
            while r.recv(1) is None:
                s.send("_ALIVE", payload="_ALIVE")

            return p  # pass control of the server process to the test

        return __server

    @pytest.fixture()
    def sender(self):
        return Sender  # for consistency with receiver

    @pytest.fixture()
    def receiver(self):
        def _receiver(*channels):
            r = Receiver(*channels, seconds_until_reconnect_attempt=2)
            time.sleep(
                0.05
            )  # let the receiver connect to the server so messages aren't dropped
            return r

        return _receiver

    def test_receiver_non_blocking(self, receiver: Callable[..., Receiver]):
        OmnibusCommunicator.server_ip = "127.0.0.1"
        sink = receiver("TEST")
        curr_time = time.perf_counter()
        sink.recv_message(0)
        after_receive_time = time.perf_counter()
        print(after_receive_time - curr_time)
        assert (
            after_receive_time - curr_time < 0.001
        )  # Less than 1 ms is acceptable, as that would be the minimum timeout otherwise

    def test_receiver_timeout_less_than_reset(self, receiver: Callable[..., Receiver]):
        OmnibusCommunicator.server_ip = "127.0.0.1"
        sink = receiver("TEST")
        curr_time = time.perf_counter()
        sink.recv_message(20)
        after_receive_time = time.perf_counter()
        print(after_receive_time - curr_time)
        assert after_receive_time - curr_time >= 0.019
        # fpt inaccuracy, inherent delays from ZMQ, platform delays, etc. makes it impossible to check upper bound accurately
        # it's not that important anyways so this is just a basic sanity check to ensure it didn't get stuck
        assert after_receive_time - curr_time <= 0.1

    def test_receiver_timeout_more_than_reset(self, receiver: Callable[..., Receiver]):
        OmnibusCommunicator.server_ip = "127.0.0.1"
        sink = receiver("TEST")
        curr_time = time.perf_counter()
        sink.recv_message(timeout=4010)
        after_receive_time = time.perf_counter()
        print(after_receive_time - curr_time)
        assert after_receive_time - curr_time >= 4.007
        assert (
            after_receive_time - curr_time <= 4.1
        )  # Factoring reset time + see above for inherent delays

    def test_infinite_time(
        self,
        start_stop_capable_server: Callable[[], SpawnProcess],
        sender: Callable[[], Sender],
        receiver: Callable[..., Receiver],
    ):
        server_process: SpawnProcess | None = None

        try:
            server_process = start_stop_capable_server()
            source: Sender = sender()
            sink: Receiver = receiver("_TESTING")
            source.send("_TESTING", "PAYLOAD")
            source.send("_TESTING", "PAYLOAD2")
            assert sink.recv() == "PAYLOAD"
            assert sink.recv() == "PAYLOAD2"
        finally:
            if server_process != None:
                server_process.terminate()
                server_process.join()
