#Tests for the WebSocket server (server2.py).

from unittest.mock import Mock, patch
import pytest
import server2

def reset():
    server2._omnibus_sender = None
    server2._bridge_sid = None

@pytest.fixture(autouse=True)
def reset_globals():
    # Reset globals before and after every test
    reset()
    yield
    reset()

class TestGetOmnibusSender:
    # Sender must be created lazily (not at import time) and reused

    @patch("server2.Sender")
    def test_sender_not_created_at_import(self, mock_sender_class):
        # Sender is not created when the module is imported
        mock_sender_class.assert_not_called()
        assert server2._omnibus_sender is None

    @patch("server2.Sender")
    def test_creates_sender_on_first_call(self, mock_sender_class):
        # Sender() is called exactly once on the first get_omnibus_sender() call
        sender = server2.get_omnibus_sender()

        mock_sender_class.assert_called_once()
        assert sender is mock_sender_class.return_value

    @patch("server2.Sender")
    def test_returns_same_instance_on_repeated_calls(self, mock_sender_class):
        # subsequent calls return the same instance
        sender1 = server2.get_omnibus_sender()
        sender2 = server2.get_omnibus_sender()

        assert sender1 is sender2
        mock_sender_class.assert_called_once()

    @patch("server2.Sender")
    def test_stores_instance_in_module_global(self, mock_sender_class):
        # created Sender is cached in _omnibus_sender
        sender = server2.get_omnibus_sender()

        assert server2._omnibus_sender is sender


class TestHandleConnect:
    # Connect handler must identify bridge via auth role and store its SID

    def test_bridge_connect_stores_sid(self):
        # bridge SID is stored when auth role is 'bridge'
        mock_request = Mock()
        mock_request.sid = "bridge-sid-123"

        with patch("server2.request", new=mock_request):
            server2.handle_connect(auth={"role": "bridge"})

        assert server2._bridge_sid == "bridge-sid-123"

    def test_regular_client_does_not_set_bridge_sid(self):
        # non-bridge client leaves _bridge_sid unchanged
        mock_request = Mock()
        mock_request.sid = "client-xyz"

        with patch("server2.request", new=mock_request):
            server2.handle_connect(auth=None)

        assert server2._bridge_sid is None

    def test_connect_with_wrong_role_does_not_set_bridge_sid(self):
        # auth with a non-bridge role does not set the bridge SID
        mock_request = Mock()
        mock_request.sid = "other-sid"

        with patch("server2.request", new=mock_request):
            server2.handle_connect(auth={"role": "client"})

        assert server2._bridge_sid is None

    def test_msgpack_exttype_auth_does_not_raise(self):
        # browser clients using msgpack send auth as ExtType (not dict)
        # isinstance(auth, dict) guard must stop a crash on .get()
        mock_request = Mock()
        mock_request.sid = "browser-sid"

        class FakeExtType:
            pass

        with patch("server2.request", new=mock_request):
            server2.handle_connect(auth=FakeExtType())  # must not raise

        assert server2._bridge_sid is None

    def test_second_bridge_overwrites_first(self):
        # bridge restart scenario: new SID replaces old one immediately
        mock_request = Mock()
        mock_request.sid = "bridge-sid-first"
        with patch("server2.request", new=mock_request):
            server2.handle_connect(auth={"role": "bridge"})
        assert server2._bridge_sid == "bridge-sid-first"

        mock_request.sid = "bridge-sid-second"
        with patch("server2.request", new=mock_request):
            server2.handle_connect(auth={"role": "bridge"})
        assert server2._bridge_sid == "bridge-sid-second"

    def test_connect_does_not_raise(self):
        # handle_connect completes without raising for any auth value
        mock_request = Mock()
        mock_request.sid = "new-client"

        with patch("server2.request", new=mock_request):
            server2.handle_connect(auth=None)  # must not raise

class TestHandleDisconnect:
    # Disconnect handler must clear bridge SID when bridge leaves

    def test_bridge_disconnect_clears_sid(self):
        # _bridge_sid is cleared when the bridge disconnects
        server2._bridge_sid = "bridge-sid-123"
        mock_request = Mock()
        mock_request.sid = "bridge-sid-123"

        with patch("server2.request", new=mock_request):
            server2.handle_disconnect()

        assert server2._bridge_sid is None

    def test_regular_client_disconnect_does_not_clear_bridge_sid(self):
        # _bridge_sid is preserved when a non-bridge client disconnects
        server2._bridge_sid = "bridge-sid-123"
        mock_request = Mock()
        mock_request.sid = "some-other-client"

        with patch("server2.request", new=mock_request):
            server2.handle_disconnect()

        assert server2._bridge_sid == "bridge-sid-123"

    def test_disconnect_does_not_raise(self):
        # handle_disconnect completes without raising
        mock_request = Mock()
        mock_request.sid = "leaving-client"

        with patch("server2.request", new=mock_request):
            server2.handle_disconnect()  # must not raise


class TestHandleChannelMessageFromBridge:
    # Messages from the bridge must be relayed to only WS clients

    def test_bridge_message_broadcast_with_skip_sid(self):
        # bridge message is emitted with skip_sid so it doesn't echo back to the bridge
        server2._bridge_sid = "bridge-sid"
        mock_request = Mock()
        mock_request.sid = "bridge-sid"

        with patch("server2.request", new=mock_request), \
             patch("server2.socketio") as mock_sio, \
             patch("server2.get_omnibus_sender"):

            server2.handle_channel_message("telemetry/altitude", [1234567890.0, {"alt": 1000}])

        mock_sio.emit.assert_called_once_with(
            "telemetry/altitude", [1234567890.0, {"alt": 1000}], skip_sid="bridge-sid"
        )

    def test_bridge_message_not_injected_into_zmq(self):
        # bridge messages must NOT be re-injected into ZMQ, would cause an infinite loop which very bad
        server2._bridge_sid = "bridge-sid"
        mock_request = Mock()
        mock_request.sid = "bridge-sid"
        mock_sender = Mock()

        with patch("server2.request", new=mock_request), \
             patch("server2.socketio"), \
             patch("server2.get_omnibus_sender", return_value=mock_sender):

            server2.handle_channel_message("telemetry", [0.0, {}])

        mock_sender.send_message.assert_not_called()


class TestHandleChannelMessageFromClient:
    # Messages from WS clients must be broadcast to all and injected into ZMQ

    def test_forwards_message_to_omnibus(self):
        # WS client message is sent to Omnibus via Sender.send_message
        mock_request = Mock()
        mock_request.sid = "client-abc"
        mock_sender = Mock()

        with patch("server2.request", new=mock_request), \
             patch("server2.socketio"), \
             patch("server2.get_omnibus_sender", return_value=mock_sender):

            server2.handle_channel_message("telemetry/altitude", [1234567890.0, {"alt": 1000}])

        mock_sender.send_message.assert_called_once()
        sent = mock_sender.send_message.call_args[0][0]
        assert sent.channel == "telemetry/altitude"
        assert sent.timestamp == 1234567890.0
        assert sent.payload == {"alt": 1000}

    def test_broadcasts_to_all_including_sender(self):
        # WS client message is broadcast to everyone (no skip_sid)
        mock_request = Mock()
        mock_request.sid = "client-abc"

        with patch("server2.request", new=mock_request), \
             patch("server2.socketio") as mock_sio, \
             patch("server2.get_omnibus_sender", return_value=Mock()):

            server2.handle_channel_message("sensors/temp", [10.0, 42])

        mock_sio.emit.assert_called_once_with("sensors/temp", [10.0, 42])
        call_kwargs = mock_sio.emit.call_args[1]
        assert "skip_sid" not in call_kwargs

    def test_uses_lazy_sender(self):
        # handle_channel_message gets the Sender through get_omnibus_sender()
        mock_request = Mock()
        mock_request.sid = "x"

        with patch("server2.request", new=mock_request), \
             patch("server2.socketio"), \
             patch("server2.get_omnibus_sender", return_value=Mock()) as mock_get:

            server2.handle_channel_message("ch", [1.0, "payload"])

        mock_get.assert_called_once()

    def test_broadcasts_before_zmq_send(self):
        # SocketIO broadcast must happen before ZMQ send
        # otherwise the bridge sees the ZMQ copy before it knows to skip it
        mock_request = Mock()
        mock_request.sid = "client-abc"

        call_order: list[str] = []
        mock_sender = Mock()
        mock_sender.send_message.side_effect = lambda _: call_order.append("zmq")

        with patch("server2.request", new=mock_request), \
             patch("server2.socketio") as mock_sio, \
             patch("server2.get_omnibus_sender", return_value=mock_sender):

            mock_sio.emit.side_effect = lambda *a, **kw: call_order.append("sio")
            server2.handle_channel_message("ch", [1.0, "data"])

        assert call_order == ["sio", "zmq"]

    def test_no_zmq_inject_for_malformed_data(self):
        # data with fewer than 2 elements does not trigger ZMQ send
        mock_request = Mock()
        mock_request.sid = "client-abc"
        mock_sender = Mock()

        with patch("server2.request", new=mock_request), \
             patch("server2.socketio"), \
             patch("server2.get_omnibus_sender", return_value=mock_sender):

            server2.handle_channel_message("ch", [1.0])  # only 1 element

        mock_sender.send_message.assert_not_called()

    def test_no_zmq_inject_for_non_list_data(self):
        # non-list data is broadcast but not injected into ZMQ
        mock_request = Mock()
        mock_request.sid = "client-abc"
        mock_sender = Mock()

        with patch("server2.request", new=mock_request), \
             patch("server2.socketio") as mock_sio, \
             patch("server2.get_omnibus_sender", return_value=mock_sender):

            server2.handle_channel_message("ch", "not-a-list")

        mock_sio.emit.assert_called_once_with("ch", "not-a-list")
        mock_sender.send_message.assert_not_called()

    def test_ws_client_message_works_without_bridge_connected(self):
        # when no bridge is connected, WS client messages still work normally
        assert server2._bridge_sid is None  # no bridge registered
        mock_request = Mock()
        mock_request.sid = "client-abc"
        mock_sender = Mock()

        with patch("server2.request", new=mock_request), \
             patch("server2.socketio") as mock_sio, \
             patch("server2.get_omnibus_sender", return_value=mock_sender):

            server2.handle_channel_message("telemetry", [1.0, {"v": 42}])

        mock_sio.emit.assert_called_once_with("telemetry", [1.0, {"v": 42}])
        mock_sender.send_message.assert_called_once()
