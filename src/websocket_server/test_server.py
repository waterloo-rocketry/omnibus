# Tests for the WebSocket server (server.py).
# Uses the Flask-SocketIO test client for integration-level tests where possible,
# falling back to mocks only for edge cases the test client can't simulate.

from unittest.mock import patch
import pytest
from socketio.packet import Packet as DefaultPacket
import server


@pytest.fixture(autouse=True)
def clean_state():
    """Reset global state and drain the relay queue before and after every test."""
    server.state.bridge_sid = None
    while not server._relay_queue.empty():
        server._relay_queue.get_nowait()
    yield
    server.state.bridge_sid = None
    while not server._relay_queue.empty():
        server._relay_queue.get_nowait()


@pytest.fixture(autouse=True)
def use_default_packet():
    """Swap the msgpack serializer for the default JSON packet class.

    The Flask-SocketIO test client constructs raw socketio.packet.Packet
    objects internally, which are incompatible with the MsgPackPacket
    class used in production. This fixture swaps the packet class for
    the duration of each test so the test client works correctly.
    The serializer choice does not affect handler logic.
    """
    original = server.socketio.server.packet_class
    server.socketio.server.packet_class = DefaultPacket
    yield
    server.socketio.server.packet_class = original


def make_bridge():
    """Create and return a test client connected as the bridge."""
    return server.socketio.test_client(
        server.app, auth={"role": "bridge"}
    )


def make_client(**kwargs):
    """Create and return a test client connected as a regular WS client."""
    return server.socketio.test_client(server.app, **kwargs)


class TestConnect:

    def test_bridge_connect_stores_sid(self):
        bridge = make_bridge()
        assert bridge.is_connected()
        assert server.state.bridge_sid is not None
        bridge.disconnect()

    def test_regular_client_does_not_set_bridge_sid(self):
        client = make_client()
        assert client.is_connected()
        assert server.state.bridge_sid is None
        client.disconnect()

    def test_connect_with_wrong_role_does_not_set_bridge_sid(self):
        client = make_client(auth={"role": "client"})
        assert client.is_connected()
        assert server.state.bridge_sid is None
        client.disconnect()

    def test_second_bridge_is_rejected(self):
        bridge1 = make_bridge()
        first_sid = server.state.bridge_sid
        assert first_sid is not None

        bridge2 = server.socketio.test_client(
            server.app, auth={"role": "bridge"}
        )
        # Second bridge should be rejected (not connected)
        assert not bridge2.is_connected()
        assert server.state.bridge_sid == first_sid
        bridge1.disconnect()

    def test_msgpack_exttype_auth_does_not_crash(self):
        # Browser clients using msgpack may send auth as ExtType (not dict).
        # The isinstance(auth, dict) guard must prevent a crash on .get().
        # The test client can't send a non-dict auth, so we call the handler directly.
        from unittest.mock import Mock
        mock_request = Mock()
        mock_request.sid = "browser-sid"

        class FakeExtType:
            pass

        with patch("server.request", new=mock_request):
            server.handle_connect(auth=FakeExtType())

        assert server.state.bridge_sid is None


class TestDisconnect:

    def test_bridge_disconnect_clears_sid(self):
        bridge = make_bridge()
        assert server.state.bridge_sid is not None
        bridge.disconnect()
        assert server.state.bridge_sid is None

    def test_regular_client_disconnect_preserves_bridge_sid(self):
        bridge = make_bridge()
        client = make_client()
        bridge_sid = server.state.bridge_sid

        client.disconnect()
        assert server.state.bridge_sid == bridge_sid
        bridge.disconnect()

    def test_disconnect_without_bridge_does_not_raise(self):
        client = make_client()
        client.disconnect()  # must not raise


class TestBridgeMessages:
    # Messages from the bridge must be relayed to WS clients but NOT to ZMQ

    def test_bridge_message_reaches_other_clients(self):
        bridge = make_bridge()
        client = make_client()
        # clear any connect-time events
        client.get_received()

        bridge.emit("telemetry/altitude", [1234567890.0, {"alt": 1000}])

        received = client.get_received()
        assert len(received) == 1
        assert received[0]["name"] == "telemetry/altitude"
        assert received[0]["args"] == [[1234567890.0, {"alt": 1000}]]

        bridge.disconnect()
        client.disconnect()

    def test_bridge_does_not_receive_own_message(self):
        bridge = make_bridge()
        client = make_client()
        bridge.get_received()  # clear

        bridge.emit("telemetry/temp", [2.0, {"temp": 25}])

        bridge_events = bridge.get_received()
        assert len(bridge_events) == 0

        bridge.disconnect()
        client.disconnect()

    def test_bridge_message_not_injected_into_zmq(self):
        bridge = make_bridge()

        bridge.emit("telemetry", [0.0, {}])

        assert server._relay_queue.empty()
        bridge.disconnect()


class TestClientMessages:
    # Messages from WS clients must be broadcast to all AND enqueued for ZMQ relay

    def test_client_message_queued_for_zmq_relay(self):
        client = make_client()

        client.emit("telemetry/altitude", [1234567890.0, {"alt": 1000}])

        assert not server._relay_queue.empty()
        msg = server._relay_queue.get_nowait()
        assert msg.channel == "telemetry/altitude/WS_ORIGINATED"
        assert msg.timestamp == 1234567890.0
        assert msg.payload == {"alt": 1000}
        client.disconnect()

    def test_client_message_broadcast_to_all(self):
        bridge = make_bridge()
        client1 = make_client()
        client2 = make_client()
        # clear connect-time events
        bridge.get_received()
        client1.get_received()
        client2.get_received()

        client1.emit("sensors/temp", [10.0, 42])

        # client1 (sender) receives its own message back (broadcast=True, no include_self=False)
        c1_events = client1.get_received()
        assert len(c1_events) == 1
        assert c1_events[0]["name"] == "sensors/temp"

        # client2 also receives it
        c2_events = client2.get_received()
        assert len(c2_events) == 1
        assert c2_events[0]["name"] == "sensors/temp"

        # bridge also receives it
        bridge_events = bridge.get_received()
        assert len(bridge_events) == 1
        assert bridge_events[0]["name"] == "sensors/temp"

        bridge.disconnect()
        client1.disconnect()
        client2.disconnect()

    def test_client_message_works_without_bridge(self):
        assert server.state.bridge_sid is None
        client = make_client()

        client.emit("telemetry", [1.0, {"v": 42}])

        # message is still broadcast
        events = client.get_received()
        assert len(events) == 1
        assert events[0]["name"] == "telemetry"
        assert events[0]["args"] == [[1.0, {"v": 42}]]

        # and still queued for ZMQ
        assert not server._relay_queue.empty()
        msg = server._relay_queue.get_nowait()
        assert msg.channel == "telemetry/WS_ORIGINATED"
        client.disconnect()

    def test_no_zmq_relay_for_malformed_data(self):
        client = make_client()

        client.emit("ch", [1.0])  # only 1 element

        assert server._relay_queue.empty()
        client.disconnect()

    def test_no_zmq_relay_for_non_list_data(self):
        client = make_client()

        client.emit("ch", "not-a-list")

        # broadcast still happens
        events = client.get_received()
        assert len(events) == 1
        assert events[0]["name"] == "ch"

        # but no ZMQ relay
        assert server._relay_queue.empty()
        client.disconnect()

    def test_broadcast_happens_before_zmq_enqueue(self):
        # SocketIO broadcast must happen before the ZMQ relay is enqueued.
        # This ordering test requires mocks since the test client can't
        # observe internal call ordering.
        from unittest.mock import Mock
        mock_request = Mock()
        mock_request.sid = "client-abc"

        call_order: list[str] = []
        original_put = server._relay_queue.put

        with patch("server.request", new=mock_request), \
             patch("server.emit") as mock_emit, \
             patch.object(server._relay_queue, "put",
                          side_effect=lambda msg: (call_order.append("zmq_enqueue"), original_put(msg))):
            mock_emit.side_effect = lambda *a, **kw: call_order.append("sio")
            server.handle_channel_message("ch", [1.0, "data"])

        assert call_order == ["sio", "zmq_enqueue"]
