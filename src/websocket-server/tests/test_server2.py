#Tests for the WebSocket server (server.py).

from unittest.mock import Mock, patch
import pytest
import server

def reset():
    server.bridge_sid = None

@pytest.fixture(autouse=True)
def reset_globals():
    # Reset globals before and after every test
    reset()
    yield
    reset()

class TestHandleConnect:
    # Connect handler must identify bridge via auth role and store its SID

    def test_bridge_connect_stores_sid(self):
        # bridge SID is stored when auth role is 'bridge'
        mock_request = Mock()
        mock_request.sid = "bridge-sid-123"

        with patch("server.request", new=mock_request):
            server.handle_connect(auth={"role": "bridge"})

        assert server.bridge_sid == "bridge-sid-123"

    def test_regular_client_does_not_set_bridge_sid(self):
        # non-bridge client leaves bridge_sid unchanged
        mock_request = Mock()
        mock_request.sid = "client-xyz"

        with patch("server.request", new=mock_request):
            server.handle_connect(auth=None)

        assert server.bridge_sid is None

    def test_connect_with_wrong_role_does_not_set_bridge_sid(self):
        # auth with a non-bridge role does not set the bridge SID
        mock_request = Mock()
        mock_request.sid = "other-sid"

        with patch("server.request", new=mock_request):
            server.handle_connect(auth={"role": "client"})

        assert server.bridge_sid is None

    def test_msgpack_exttype_auth_does_not_raise(self):
        # browser clients using msgpack send auth as ExtType (not dict)
        # isinstance(auth, dict) guard must stop a crash on .get()
        mock_request = Mock()
        mock_request.sid = "browser-sid"

        class FakeExtType:
            pass

        with patch("server.request", new=mock_request):
            server.handle_connect(auth=FakeExtType())  # must not raise

        assert server.bridge_sid is None

    def test_second_bridge_overwrites_first(self):
        # bridge restart scenario: new SID replaces old one immediately
        mock_request = Mock()
        mock_request.sid = "bridge-sid-first"
        with patch("server.request", new=mock_request):
            server.handle_connect(auth={"role": "bridge"})
        assert server.bridge_sid == "bridge-sid-first"

        mock_request.sid = "bridge-sid-second"
        with patch("server.request", new=mock_request):
            server.handle_connect(auth={"role": "bridge"})
        assert server.bridge_sid == "bridge-sid-second"

    def test_connect_does_not_raise(self):
        # handle_connect completes without raising for any auth value
        mock_request = Mock()
        mock_request.sid = "new-client"

        with patch("server.request", new=mock_request):
            server.handle_connect(auth=None)  # must not raise

class TestHandleDisconnect:
    # Disconnect handler must clear bridge SID when bridge leaves

    def test_bridge_disconnect_clears_sid(self):
        # _bridge_sid is cleared when the bridge disconnects
        server.bridge_sid = "bridge-sid-123"
        mock_request = Mock()
        mock_request.sid = "bridge-sid-123"

        with patch("server.request", new=mock_request):
            server.handle_disconnect()

        assert server.bridge_sid is None

    def test_regular_client_disconnect_does_not_clear_bridge_sid(self):
        # _bridge_sid is preserved when a non-bridge client disconnects
        server.bridge_sid = "bridge-sid-123"
        mock_request = Mock()
        mock_request.sid = "some-other-client"

        with patch("server.request", new=mock_request):
            server.handle_disconnect()

        assert server.bridge_sid == "bridge-sid-123"

    def test_disconnect_does_not_raise(self):
        # handle_disconnect completes without raising
        mock_request = Mock()
        mock_request.sid = "leaving-client"

        with patch("server.request", new=mock_request):
            server.handle_disconnect()  # must not raise


class TestHandleChannelMessageFromBridge:
    # Messages from the bridge must be relayed to only WS clients

    def test_bridge_message_broadcast_with_include_self_false(self):
        # bridge message is emitted with skip_sid so it doesn't echo back to the bridge
        server.bridge_sid = "bridge-sid"
        mock_request = Mock()
        mock_request.sid = "bridge-sid"

        with patch("server.request", new=mock_request), \
             patch("server.emit") as mock_sio, \
             patch("server.Sender") as mock_sender_class:

            server.handle_channel_message("telemetry/altitude", [1234567890.0, {"alt": 1000}])

        mock_sio.assert_called_once_with(
            "telemetry/altitude", [1234567890.0, {"alt": 1000}], broadcast=True, include_self=False
        )

    def test_bridge_message_not_injected_into_zmq(self):
        # bridge messages must NOT be re-injected into ZMQ, would cause an infinite loop which very bad
        server.bridge_sid = "bridge-sid"
        mock_request = Mock()
        mock_request.sid = "bridge-sid"

        with patch("server.request", new=mock_request), \
             patch("server.emit"), \
             patch("server.Sender") as mock_sender_class:

            server.handle_channel_message("telemetry", [0.0, {}])

        mock_instance = mock_sender_class.return_value
        mock_instance.send_message.assert_not_called()


class TestHandleChannelMessageFromClient:
    # Messages from WS clients must be broadcast to all and injected into ZMQ

    def test_forwards_message_to_omnibus(self):
        # WS client message is sent to Omnibus via Sender.send_message
        mock_request = Mock()
        mock_request.sid = "client-abc"

        with patch("server.request", new=mock_request), \
             patch("server.emit"), \
             patch("server.Sender") as mock_sender_class:

            server.handle_channel_message("telemetry/altitude", [1234567890.0, {"alt": 1000}])
        
        mock_instance = mock_sender_class.return_value
        mock_instance.send_message.assert_called_once()
        sent = mock_instance.send_message.call_args[0][0]
        assert sent.channel == "telemetry/altitude/WS_ORIGINATED"
        assert sent.timestamp == 1234567890.0
        assert sent.payload == {"alt": 1000}

    def test_broadcasts_to_all_including_sender(self):
        # WS client message is broadcast to everyone (no skip_sid)
        mock_request = Mock()
        mock_request.sid = "client-abc"

        with patch("server.request", new=mock_request), \
             patch("server.emit") as mock_sio, \
             patch("server.Sender") as mock_sender_class:

            server.handle_channel_message("sensors/temp", [10.0, 42])

        mock_sio.assert_called_once()
        args, kwargs = mock_sio.call_args
        assert args == ("sensors/temp", [10.0, 42])
        assert "skip_sid" not in kwargs
        assert kwargs.get("broadcast") == True

    

    def test_broadcasts_before_zmq_send(self):
        # SocketIO broadcast must happen before ZMQ send
        # otherwise the bridge sees the ZMQ copy before it knows to skip it
        mock_request = Mock()
        mock_request.sid = "client-abc"

        call_order: list[str] = []
        mock_sender = Mock()
        mock_sender.send_message.side_effect = lambda _: call_order.append("zmq")

        with patch("server.request", new=mock_request), \
             patch("server.emit") as mock_emit, \
             patch("server.Sender") as mock_sender_class:
            
            mock_sender_class.return_value.send_message.side_effect = lambda _: call_order.append("zmq")
            mock_emit.side_effect = lambda *a, **kw: call_order.append("sio")
            server.handle_channel_message("ch", [1.0, "data"])

        assert call_order == ["sio", "zmq"]

    def test_no_zmq_inject_for_malformed_data(self):
        # data with fewer than 2 elements does not trigger ZMQ send
        mock_request = Mock()
        mock_request.sid = "client-abc"

        with patch("server.request", new=mock_request), \
             patch("server.emit"), \
                patch("server.Sender") as mock_sender_class:

            server.handle_channel_message("ch", [1.0])  # only 1 element
        
        mock_instance = mock_sender_class.return_value
        mock_instance.send_message.assert_not_called()

    def test_no_zmq_inject_for_non_list_data(self):
        # non-list data is broadcast but not injected into ZMQ
        mock_request = Mock()
        mock_request.sid = "client-abc"

        with patch("server.request", new=mock_request), \
             patch("server.emit") as mock_sio, \
             patch("server.Sender") as mock_sender_class:

            server.handle_channel_message("ch", "not-a-list")

        mock_instance = mock_sender_class.return_value
        mock_sio.assert_called_once()
        args, kwargs = mock_sio.call_args
        assert args == ("ch", "not-a-list")
        assert kwargs.get("broadcast") == True
        mock_instance.send_message.assert_not_called()

    def test_ws_client_message_works_without_bridge_connected(self):
        # when no bridge is connected, WS client messages still work normally
        assert server.bridge_sid is None  # no bridge registered
        mock_request = Mock()
        mock_request.sid = "client-abc"

        with patch("server.request", new=mock_request), \
             patch("server.emit") as mock_sio, \
             patch("server.Sender") as mock_sender_class:

            server.handle_channel_message("telemetry", [1.0, {"v": 42}])
        
        mock_instance = mock_sender_class.return_value
        mock_sio.assert_called_once()
        args, kwargs = mock_sio.call_args
        assert args == ("telemetry", [1.0, {"v": 42}])
        assert kwargs.get("broadcast") == True
        mock_instance.send_message.assert_called_once()
