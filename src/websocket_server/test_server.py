# pyright: standard
# Tests for the WebSocket server (server.py).

import socket
import threading
import time
from unittest.mock import Mock, patch

import pytest
import socketio
from socketio.exceptions import ConnectionError, TimeoutError

import server
from omnibus import Message as OmnibusMessage


@pytest.fixture(scope="session")
def server_url():
    """Start the SocketIO server on a free port in a daemon thread."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        port = s.getsockname()[1]

    url = f"http://127.0.0.1:{port}"

    threading.Thread(
        target=lambda: server.socketio.run(
            server.app, host="127.0.0.1", port=port,
            log_output=False, allow_unsafe_werkzeug=True,
        ),
        daemon=True,
    ).start()

    probe = socketio.SimpleClient(serializer="msgpack")
    for _ in range(50):
        try:
            probe.connect(url)
            probe.disconnect()
            break
        except Exception:
            time.sleep(0.1)
    else:
        raise RuntimeError("Server did not start in time")

    yield url


@pytest.fixture(autouse=True)
def clean_state():
    server.state.bridge_sid = None
    while not server._relay_queue.empty():
        server._relay_queue.get_nowait()
    yield
    server.state.bridge_sid = None
    while not server._relay_queue.empty():
        server._relay_queue.get_nowait()


def make_bridge(url):
    c = socketio.SimpleClient(serializer="msgpack")
    c.connect(url, auth={"role": "bridge"})
    return c


def make_client(url):
    c = socketio.SimpleClient(serializer="msgpack")
    c.connect(url)
    return c


class TestConnect:

    def test_bridge_connect_stores_sid(self, server_url):
        bridge = make_bridge(server_url)
        try:
            assert server.state.bridge_sid is not None
        finally:
            bridge.disconnect()

    def test_regular_client_does_not_set_bridge_sid(self, server_url):
        client = make_client(server_url)
        try:
            assert server.state.bridge_sid is None
        finally:
            client.disconnect()

    def test_connect_with_wrong_role_does_not_set_bridge_sid(self, server_url):
        client = socketio.SimpleClient(serializer="msgpack")
        client.connect(server_url, auth={"role": "client"})
        try:
            assert server.state.bridge_sid is None
        finally:
            client.disconnect()

    def test_second_bridge_is_rejected(self, server_url):
        first = make_bridge(server_url)
        try:
            first_sid = server.state.bridge_sid
            assert first_sid is not None

            with pytest.raises(ConnectionError):
                make_bridge(server_url)

            assert server.state.bridge_sid == first_sid
        finally:
            first.disconnect()

    def test_msgpack_exttype_auth_does_not_crash(self):
        # Browser clients using msgpack send auth as ExtType, not dict.
        # Can't send non-dict auth from a real client — must be mocked.
        mock_request = Mock()
        mock_request.sid = "browser-sid"

        class FakeExtType:
            pass

        with patch("server.request", new=mock_request):
            server.handle_connect(auth=FakeExtType())

        assert server.state.bridge_sid is None


class TestDisconnect:

    def test_bridge_disconnect_clears_sid(self, server_url):
        bridge = make_bridge(server_url)
        assert server.state.bridge_sid is not None
        bridge.disconnect()
        time.sleep(0.2)
        assert server.state.bridge_sid is None

    def test_regular_client_disconnect_preserves_bridge_sid(self, server_url):
        bridge = make_bridge(server_url)
        client = make_client(server_url)
        bridge_sid = server.state.bridge_sid
        assert bridge_sid is not None

        client.disconnect()
        time.sleep(0.2)

        try:
            assert server.state.bridge_sid == bridge_sid
        finally:
            bridge.disconnect()

    def test_disconnect_without_bridge_does_not_raise(self, server_url):
        client = make_client(server_url)
        client.disconnect()


class TestBridgeMessages:

    def test_bridge_message_reaches_other_clients(self, server_url):
        bridge = make_bridge(server_url)
        client = make_client(server_url)
        try:
            bridge.emit("telemetry/altitude", [1234567890.0, {"alt": 1000}])
            event, data = client.receive(timeout=2)
            assert event == "telemetry/altitude"
            assert data == [1234567890.0, {"alt": 1000}]
        finally:
            client.disconnect()
            bridge.disconnect()

    def test_bridge_does_not_receive_own_message(self, server_url):
        bridge = make_bridge(server_url)
        try:
            bridge.emit("telemetry/temp", [0.0, 42])
            with pytest.raises(TimeoutError):
                bridge.receive(timeout=0.5)
        finally:
            bridge.disconnect()

    def test_bridge_message_not_injected_into_zmq(self, server_url):
        # Re-injecting bridge messages into ZMQ would cause an infinite loop.
        bridge = make_bridge(server_url)
        client = make_client(server_url)
        try:
            bridge.emit("telemetry", [0.0, {}])
            client.receive(timeout=2)
            assert server._relay_queue.empty()
        finally:
            client.disconnect()
            bridge.disconnect()


class TestClientMessages:

    def test_client_message_queued_for_zmq_relay(self, server_url):
        client = make_client(server_url)
        try:
            client.emit("telemetry/altitude", [1234567890.0, {"alt": 1000}])
            client.receive(timeout=2)
            time.sleep(0.1)

            assert not server._relay_queue.empty()
            sent = server._relay_queue.get_nowait()
            assert sent.channel == "telemetry/altitude/WS_ORIGINATED"
            assert sent.timestamp == 1234567890.0
            assert sent.payload == {"alt": 1000}
        finally:
            client.disconnect()

    def test_client_message_broadcast_to_all(self, server_url):
        bridge = make_bridge(server_url)
        client1 = make_client(server_url)
        client2 = make_client(server_url)
        try:
            client1.emit("sensors/temp", [10.0, 42])

            e1, d1 = bridge.receive(timeout=2)
            e2, d2 = client1.receive(timeout=2)
            e3, d3 = client2.receive(timeout=2)

            for e in (e1, e2, e3):
                assert e == "sensors/temp"
            for d in (d1, d2, d3):
                assert d == [10.0, 42]
        finally:
            client2.disconnect()
            client1.disconnect()
            bridge.disconnect()

    def test_client_message_works_without_bridge(self, server_url):
        assert server.state.bridge_sid is None
        client = make_client(server_url)
        try:
            client.emit("telemetry", [1.0, {"v": 42}])

            event, data = client.receive(timeout=2)
            assert event == "telemetry"
            assert data == [1.0, {"v": 42}]

            time.sleep(0.1)
            assert not server._relay_queue.empty()
            sent = server._relay_queue.get_nowait()
            assert sent.channel == "telemetry/WS_ORIGINATED"
        finally:
            client.disconnect()

    def test_no_zmq_relay_for_malformed_data(self, server_url):
        client = make_client(server_url)
        try:
            client.emit("ch", [1.0])
            client.receive(timeout=2)
            time.sleep(0.1)
            assert server._relay_queue.empty()
        finally:
            client.disconnect()

    def test_no_zmq_relay_for_non_list_data(self, server_url):
        client = make_client(server_url)
        try:
            client.emit("ch", "not-a-list")
            event, data = client.receive(timeout=2)
            assert event == "ch"
            assert data == "not-a-list"
            time.sleep(0.1)
            assert server._relay_queue.empty()
        finally:
            client.disconnect()

    def test_broadcast_happens_before_zmq_enqueue(self):
        # Internal ordering — must be mocked to instrument call sequence.
        mock_request = Mock()
        mock_request.sid = "client-abc"

        call_order: list[str] = []
        original_put = server._relay_queue.put

        with patch("server.request", new=mock_request), \
             patch("server.emit") as mock_emit, \
             patch.object(
                 server._relay_queue, "put",
                 side_effect=lambda msg: (
                     call_order.append("zmq_enqueue"), original_put(msg)
                 ),
             ):
            mock_emit.side_effect = lambda *a, **kw: call_order.append("sio")
            server.handle_channel_message("ch", [1.0, "data"])

        assert call_order == ["sio", "zmq_enqueue"]


class _StopLoop(Exception):
    pass

class TestRelaySender:

    def test_relay_sender_thread_forwards_to_zmq(self):
        # Capture _sender_loop instead of spawning a real thread to avoid
        # a persistent consumer racing with other tests for _relay_queue.
        captured_target = []

        with patch.object(
            server.socketio, "start_background_task",
            side_effect=lambda fn: captured_target.append(fn),
        ):
            server.start_relay_sender()

        assert len(captured_target) == 1

        mock_sender = Mock()
        msg = OmnibusMessage("test/WS_ORIGINATED", 1.0, {"v": 1})

        with patch("server.Sender", return_value=mock_sender), \
             patch.object(
                 server._relay_queue, "get", side_effect=[msg, _StopLoop],
             ):
            with pytest.raises(_StopLoop):
                captured_target[0]()

        mock_sender.send_message.assert_called_once_with(msg)
