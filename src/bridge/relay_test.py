#Tests for the bridge relay server

import pytest
from unittest.mock import Mock, patch
from socketio import exceptions
import relay

# Helper capture @sio.on callbacks registered inside main()
def _make_capturing_sio():
    # intercepts sio.on() so we can grab the callbacks main() registers
    # after main() runs, call callbacks["*"]("ch", [ts, data]) to simulate a WS broadcast
    mock_sio = Mock()
    callbacks: dict = {}

    def on_factory(event):
        def store(f):
            callbacks[event] = f
            return f
        return store

    mock_sio.on.side_effect = on_factory
    return mock_sio, ""

# Auto-discovery and setup

class TestAutoDiscovery:
    #The bridge must use Omnibus auto-discovery

    @patch("relay.time")
    @patch("relay.Receiver")
    @patch("relay.socketio.Client")
    def test_receiver_subscribes_to_all_channels(self, mock_client_class, mock_receiver_class, mock_time):
        # Reciever captures all omnibus channels
        mock_sio, _ = _make_capturing_sio()
        mock_client_class.return_value = mock_sio
        mock_receiver = Mock()
        mock_receiver.recv_message.side_effect = SystemExit()
        mock_receiver_class.return_value = mock_receiver

        with pytest.raises(SystemExit):
            relay.main()

        mock_receiver_class.assert_called_once_with("")

    @patch("relay.time")
    @patch("relay.Receiver")
    @patch("relay.socketio.Client")
    def test_socketio_client_uses_msgpack_serializer(self, mock_client_class, mock_receiver_class, mock_time):
        # Must use msgpack
        mock_sio, _ = _make_capturing_sio()
        mock_client_class.return_value = mock_sio
        mock_receiver = Mock()
        mock_receiver.recv_message.side_effect = SystemExit()
        mock_receiver_class.return_value = mock_receiver

        with pytest.raises(SystemExit):
            relay.main()

        mock_client_class.assert_called_once_with(logger=False, engineio_logger=False, serializer="msgpack", reconnection=False)

    @patch("relay.time")
    @patch("relay.Receiver")
    @patch("relay.socketio.Client")
    def test_does_not_preset_server_ip(self, mock_client_class, mock_receiver_class, mock_time):
        # must not preset server_ip — let omnibus auto-discover it
        
        from omnibus.omnibus import OmnibusCommunicator

        mock_sio, _ = _make_capturing_sio()
        mock_client_class.return_value = mock_sio
        mock_receiver = Mock()
        mock_receiver.recv_message.side_effect = SystemExit()
        mock_receiver_class.return_value = mock_receiver

        OmnibusCommunicator.server_ip = None

        with pytest.raises(SystemExit):
            relay.main()

        assert OmnibusCommunicator.server_ip is None

# Relay loop

class TestRelayLoop:
    #ZMQ messages must be forwarded to the WebSocket server via SocketIO

    @patch("relay.time")
    @patch("relay.Receiver")
    @patch("relay.socketio.Client")
    def test_uses_blocking_receive(self, mock_client_class, mock_receiver_class, mock_time):
        # Confirm recv_message is called with None
        mock_sio, _ = _make_capturing_sio()
        mock_client_class.return_value = mock_sio
        mock_receiver = Mock()
        mock_receiver.recv_message.side_effect = SystemExit()
        mock_receiver_class.return_value = mock_receiver

        with pytest.raises(SystemExit):
            relay.main()

        mock_receiver.recv_message.assert_called_with(None)

    @patch("relay.time")
    @patch("relay.Receiver")
    @patch("relay.socketio.Client")
    
    def test_emits_message_with_correct_channel(self, mock_client_class, mock_receiver_class, mock_time):
        # Each received ZMQ message is emitted on the correct channel
        mock_sio, _ = _make_capturing_sio()
        mock_client_class.return_value = mock_sio

        msg = Mock()
        msg.channel = "sensors/temperature"
        msg.timestamp = 1234567890.0
        msg.payload = {"value": 25.5}

        mock_receiver = Mock()
        mock_receiver.recv_message.side_effect = [msg, SystemExit()]
        mock_receiver_class.return_value = mock_receiver

        with pytest.raises(SystemExit):
            relay.main()

        mock_sio.emit.assert_called_once_with("sensors/temperature", [1234567890.0, {"value": 25.5}])

    @patch("relay.time")
    @patch("relay.Receiver")
    @patch("relay.socketio.Client")
    def test_emits_timestamp_and_payload_as_list(self, mock_client_class, mock_receiver_class, mock_time):
        #Data is forwarded as [timestamp, payload] to match the wire format
        mock_sio, _ = _make_capturing_sio()
        mock_client_class.return_value = mock_sio

        msg = Mock()
        msg.channel = "telemetry"
        msg.timestamp = 42.0
        msg.payload = "raw_data"

        mock_receiver = Mock()
        mock_receiver.recv_message.side_effect = [msg, SystemExit()]
        mock_receiver_class.return_value = mock_receiver

        with pytest.raises(SystemExit):
            relay.main()

        assert mock_sio.emit.call_args[0][1] == [42.0, "raw_data"]

class TestLoopBackPrevention:
    #Messages injected into ZMQ by the WS server must not be re-relayed

    @patch("relay.time")
    @patch("relay.Receiver")
    @patch("relay.socketio.Client")
    def test_ws_originated_message_is_skipped(self, mock_client_class, mock_receiver_class, mock_time):
        #When the WS server has already broadcast (channel, ts), the matching ZMQ message is dropped so WS clients don't receive it twice.
        mock_sio, _ = _make_capturing_sio()
        mock_client_class.return_value = mock_sio

        msg = Mock()
        msg.channel = "sensors/temp/WS_ORIGINATED"
        msg.timestamp = 123.0
        msg.payload = {"v": 1}

        calls = [0]

        def recv_side_effect(timeout):
            calls[0] += 1
            if calls[0] == 1:
                # Message with WS_ORIGINATED suffix should be skipped
                return msg
            raise SystemExit()

        mock_receiver = Mock()
        mock_receiver.recv_message.side_effect = recv_side_effect
        mock_receiver_class.return_value = mock_receiver

        with pytest.raises(SystemExit):
            relay.main()

        mock_sio.emit.assert_not_called()

    @patch("relay.time")
    @patch("relay.Receiver")
    @patch("relay.socketio.Client")
    def test_non_ws_originated_message_is_relayed(self, mock_client_class, mock_receiver_class, mock_time):
        #A ZMQ message with no matching WS broadcast is relayed normally
        mock_sio, _ = _make_capturing_sio()
        mock_client_class.return_value = mock_sio

        msg = Mock()
        msg.channel = "telemetry"
        msg.timestamp = 999.0
        msg.payload = "data"

        mock_receiver = Mock()
        # no WS suffix, so it's a real ZMQ-only message
        mock_receiver.recv_message.side_effect = [msg, SystemExit()]
        mock_receiver_class.return_value = mock_receiver

        with pytest.raises(SystemExit):
            relay.main()

        mock_sio.emit.assert_called_once_with("telemetry", [999.0, "data"])

    @patch("relay.time")
    @patch("relay.Receiver")
    @patch("relay.socketio.Client")
    def test_ws_originated_message_with_similar_channel_is_not_skipped(self, mock_client_class, mock_receiver_class, mock_time):
        #Only messages with the exact WS_ORIGINATED_SUFFIX should be skipped, not messages on similar channels
        mock_sio, _ = _make_capturing_sio()
        mock_client_class.return_value = mock_sio

        msg = Mock()
        msg.channel = "telemetry/WS_ORIGINATED/extra"
        msg.timestamp = 555.0
        msg.payload = "x"

        mock_receiver = Mock()
        mock_receiver.recv_message.side_effect = [msg, SystemExit()]
        mock_receiver_class.return_value = mock_receiver

        with pytest.raises(SystemExit):
            relay.main()

        # This message should be relayed because the channel doesn't end with the exact suffix
        mock_sio.emit.assert_called_once_with("telemetry/WS_ORIGINATED/extra", [555.0, "x"])

# Connection retry
class TestConnectionRetry:
    #The bridge must keep trying to reach the WebSocket server on startup.

    @patch("relay.time")
    @patch("relay.Receiver")
    @patch("relay.socketio.Client")
    def test_retries_on_connection_error(self, mock_client_class, mock_receiver_class, mock_time):
        #Bridge retries if the WebSocket server is not yet available
        from socketio.exceptions import ConnectionError as SioConnectionError

        mock_sio, _ = _make_capturing_sio()
        mock_client_class.return_value = mock_sio
        mock_sio.connect.side_effect = [SioConnectionError(), None]

        mock_receiver = Mock()
        mock_receiver.recv_message.side_effect = SystemExit()
        mock_receiver_class.return_value = mock_receiver
        mock_time.sleep = Mock()

        with pytest.raises(SystemExit):
            relay.main()

        assert mock_sio.connect.call_count == 2

    @patch("relay.time")
    @patch("relay.Receiver")
    @patch("relay.socketio.Client")
    def test_sleeps_between_connection_retries(self, mock_client_class, mock_receiver_class, mock_time):
        #Bridge sleeps for 1 second between each reconnection attempt
        from socketio.exceptions import ConnectionError as SioConnectionError

        mock_sio, _ = _make_capturing_sio()
        mock_client_class.return_value = mock_sio
        mock_sio.connect.side_effect = [SioConnectionError(), None]

        mock_receiver = Mock()
        mock_receiver.recv_message.side_effect = SystemExit()
        mock_receiver_class.return_value = mock_receiver
        mock_time.sleep = Mock()

        with pytest.raises(SystemExit):
            relay.main()

        mock_time.sleep.assert_any_call(1)

    @patch("relay.time")
    @patch("relay.Receiver")
    @patch("relay.socketio.Client")
    def test_connects_with_bridge_auth(self, mock_client_class, mock_receiver_class, mock_time):
        #Bridge identifies itself to the WS server via auth role='bridge'
        mock_sio, _ = _make_capturing_sio()
        mock_client_class.return_value = mock_sio

        mock_receiver = Mock()
        mock_receiver.recv_message.side_effect = SystemExit()
        mock_receiver_class.return_value = mock_receiver

        with pytest.raises(SystemExit):
            relay.main()

        mock_sio.connect.assert_called_once_with(
            "http://127.0.0.1:6767", auth={"role": "bridge"}
        )

# Mid-run reconnection
class TestMidRunReconnection:
    #Bridge must recover if server2 goes down

    @patch("relay.time")
    @patch("relay.Receiver")
    @patch("relay.socketio.Client")
    def test_reconnects_when_disconnected_before_emit(self, mock_client_class, mock_receiver_class, mock_time):
        #If sio.connected is False when a message arrives, bridge reconnects
        
        mock_sio, _ = _make_capturing_sio()
        mock_client_class.return_value = mock_sio

        # connect() sets connected=True so the relay loop can proceed.
        def on_connect(*args, **kwargs):
            mock_sio.connected = True

        mock_sio.connect.side_effect = on_connect
        mock_sio.connected = True  # starts connected

        msg = Mock()
        msg.channel = "telemetry"
        msg.timestamp = 1.0
        msg.payload = "x"

        calls = [0]

        def recv_side_effect(timeout):
            calls[0] += 1
            if calls[0] == 1:
                # Simulate server2 dying between messages
                mock_sio.connected = False
                return msg
            raise SystemExit()

        mock_receiver = Mock()
        mock_receiver.recv_message.side_effect = recv_side_effect
        mock_receiver_class.return_value = mock_receiver

        with pytest.raises(SystemExit):
            relay.main()

        # Initial connect + one reconnect after the drop
        assert mock_sio.connect.call_count == 2
        mock_sio.disconnect.assert_called_once()

    @patch("relay.time")
    @patch("relay.Receiver")
    @patch("relay.socketio.Client")
    def test_reconnects_on_emit_failure(self, mock_client_class, mock_receiver_class, mock_time):
        #If sio.emit raises (server dropped mid-relay), bridge reconnects
        mock_sio, _ = _make_capturing_sio()
        mock_client_class.return_value = mock_sio
        mock_sio.connected = True

        msg = Mock()
        msg.channel = "telemetry"
        msg.timestamp = 2.0
        msg.payload = "y"

        mock_sio.emit.side_effect = [exceptions.ConnectionError("dropped"), None]

        mock_receiver = Mock()
        mock_receiver.recv_message.side_effect = [msg, SystemExit()]
        mock_receiver_class.return_value = mock_receiver

        with pytest.raises(SystemExit):
            relay.main()

        # Initial connect + reconnect triggered by emit failure
        assert mock_sio.connect.call_count == 2
        mock_sio.disconnect.assert_called_once()

    @patch("relay.time")
    @patch("relay.Receiver")
    @patch("relay.socketio.Client")
    def test_reconnect_survives_disconnect_raising(self, mock_client_class, mock_receiver_class, mock_time):
        #If sio.disconnect() raises during reconnect, the bridge still reconnects
        mock_sio, _ = _make_capturing_sio()
        mock_client_class.return_value = mock_sio
        mock_sio.connected = True
        mock_sio.disconnect.side_effect = Exception("already dead")

        msg = Mock()
        msg.channel = "ch"
        msg.timestamp = 1.0
        msg.payload = "x"

        mock_sio.emit.side_effect = [exceptions.ConnectionError("dropped"), None]

        mock_receiver = Mock()
        mock_receiver.recv_message.side_effect = [msg, SystemExit()]
        mock_receiver_class.return_value = mock_receiver

        with pytest.raises(SystemExit):
            relay.main()

        # disconnect raised but connect was still called (reconnect proceeded)
        assert mock_sio.connect.call_count == 2

    @patch("relay.time")
    @patch("relay.Receiver")
    @patch("relay.socketio.Client")
    def test_reconnect_uses_bridge_auth(self, mock_client_class, mock_receiver_class, mock_time):
        #Reconnect still authenticates as bridge, not as a plain client
        mock_sio, _ = _make_capturing_sio()
        mock_client_class.return_value = mock_sio
        mock_sio.connected = True

        msg = Mock()
        msg.channel = "ch"
        msg.timestamp = 3.0
        msg.payload = "z"

        mock_sio.emit.side_effect = [exceptions.ConnectionError("dropped"), None]

        mock_receiver = Mock()
        mock_receiver.recv_message.side_effect = [msg, SystemExit()]
        mock_receiver_class.return_value = mock_receiver

        with pytest.raises(SystemExit):
            relay.main()

        for call in mock_sio.connect.call_args_list:
            assert call == (("http://127.0.0.1:6767",), {"auth": {"role": "bridge"}}), (
                f"Expected bridge auth on every connect call, got: {call}"
            )

    @patch("relay.time")
    @patch("relay.Receiver")
    @patch("relay.socketio.Client")
    def test_unexpected_emit_exception_propagates(self, mock_client_class, mock_receiver_class, mock_time):
        # non-connection exceptions on emit should bubble up, not be swallowed
        mock_sio, _ = _make_capturing_sio()
        mock_client_class.return_value = mock_sio
        mock_sio.connected = True

        msg = Mock()
        msg.channel = "ch"
        msg.timestamp = 1.0
        msg.payload = "x"

        mock_sio.emit.side_effect = RuntimeError("unexpected")

        mock_receiver = Mock()
        mock_receiver.recv_message.side_effect = [msg]
        mock_receiver_class.return_value = mock_receiver

        with pytest.raises(RuntimeError, match="unexpected"):
            relay.main()
