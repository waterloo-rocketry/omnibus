"""Tests for ZeroMQ client."""

import pytest
from unittest.mock import Mock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from zmq_client import ZmqReceiver, DEFAULT_SERVER_IP
from translator import Message


class TestZmqReceiver:
    """Tests for the ZmqReceiver class."""

    @patch('zmq_client.Receiver')
    @patch('zmq_client.OmnibusCommunicator')
    def test_init_sets_server_ip(self, mock_communicator, mock_receiver):
        """Verify that initialization sets the server IP."""
        ZmqReceiver(server_ip="192.168.1.100")
        assert mock_communicator.server_ip == "192.168.1.100"

    @patch('zmq_client.Receiver')
    @patch('zmq_client.OmnibusCommunicator')
    def test_init_uses_default_ip(self, mock_communicator, mock_receiver):
        """Verify that default server IP is used when not specified."""
        ZmqReceiver()
        assert mock_communicator.server_ip == DEFAULT_SERVER_IP

    @patch('zmq_client.Receiver')
    @patch('zmq_client.OmnibusCommunicator')
    def test_init_subscribes_to_all_channels_by_default(self, mock_communicator, mock_receiver):
        """Verify that receiver subscribes to all channels by default."""
        ZmqReceiver()
        mock_receiver.assert_called_once_with("")

    @patch('zmq_client.Receiver')
    @patch('zmq_client.OmnibusCommunicator')
    def test_init_subscribes_to_specified_channels(self, mock_communicator, mock_receiver):
        """Verify that receiver subscribes to specified channels."""
        ZmqReceiver(channels=("sensors", "commands"))
        mock_receiver.assert_called_once_with("sensors", "commands")

    @patch('zmq_client.Receiver')
    @patch('zmq_client.OmnibusCommunicator')
    def test_receive_returns_message(self, mock_communicator, mock_receiver_class):
        """Verify that receive returns a properly converted Message."""
        # Create a mock omnibus message
        mock_omnibus_msg = Mock()
        mock_omnibus_msg.channel = "sensors/temperature"
        mock_omnibus_msg.timestamp = 1737745200.123
        mock_omnibus_msg.payload = {"value": 25.5}

        # Configure the mock receiver to return our message
        mock_receiver_instance = Mock()
        mock_receiver_instance.recv_message.return_value = mock_omnibus_msg
        mock_receiver_class.return_value = mock_receiver_instance

        receiver = ZmqReceiver()
        msg = receiver.receive()

        assert msg is not None
        assert msg.channel == "sensors/temperature"
        assert msg.timestamp == 1737745200.123
        assert msg.payload == {"value": 25.5}

    @patch('zmq_client.Receiver')
    @patch('zmq_client.OmnibusCommunicator')
    def test_receive_returns_none_on_timeout(self, mock_communicator, mock_receiver_class):
        """Verify that receive returns None when no message is available."""
        mock_receiver_instance = Mock()
        mock_receiver_instance.recv_message.return_value = None
        mock_receiver_class.return_value = mock_receiver_instance

        receiver = ZmqReceiver()
        msg = receiver.receive()

        assert msg is None

    @patch('zmq_client.Receiver')
    @patch('zmq_client.OmnibusCommunicator')
    def test_receive_passes_timeout(self, mock_communicator, mock_receiver_class):
        """Verify that receive passes the timeout parameter correctly."""
        mock_receiver_instance = Mock()
        mock_receiver_instance.recv_message.return_value = None
        mock_receiver_class.return_value = mock_receiver_instance

        receiver = ZmqReceiver()
        receiver.receive(timeout_ms=500)

        mock_receiver_instance.recv_message.assert_called_with(timeout=500)

    @patch('zmq_client.Receiver')
    @patch('zmq_client.OmnibusCommunicator')
    def test_receive_default_timeout(self, mock_communicator, mock_receiver_class):
        """Verify that receive uses default timeout of 100ms."""
        mock_receiver_instance = Mock()
        mock_receiver_instance.recv_message.return_value = None
        mock_receiver_class.return_value = mock_receiver_instance

        receiver = ZmqReceiver()
        receiver.receive()

        mock_receiver_instance.recv_message.assert_called_with(timeout=100)

    @patch('zmq_client.Receiver')
    @patch('zmq_client.OmnibusCommunicator')
    def test_receive_returns_correct_message_type(self, mock_communicator, mock_receiver_class):
        """Verify that receive returns our Message type, not omnibus.Message."""
        mock_omnibus_msg = Mock()
        mock_omnibus_msg.channel = "test"
        mock_omnibus_msg.timestamp = 100.0
        mock_omnibus_msg.payload = "data"

        mock_receiver_instance = Mock()
        mock_receiver_instance.recv_message.return_value = mock_omnibus_msg
        mock_receiver_class.return_value = mock_receiver_instance

        receiver = ZmqReceiver()
        msg = receiver.receive()

        assert isinstance(msg, Message)


class TestZmqReceiverPayloadTypes:
    """Tests for handling various payload types."""

    @patch('zmq_client.Receiver')
    @patch('zmq_client.OmnibusCommunicator')
    def test_receive_with_dict_payload(self, mock_communicator, mock_receiver_class):
        """Verify dict payloads are handled correctly."""
        mock_omnibus_msg = Mock()
        mock_omnibus_msg.channel = "test"
        mock_omnibus_msg.timestamp = 100.0
        mock_omnibus_msg.payload = {"nested": {"data": [1, 2, 3]}}

        mock_receiver_instance = Mock()
        mock_receiver_instance.recv_message.return_value = mock_omnibus_msg
        mock_receiver_class.return_value = mock_receiver_instance

        receiver = ZmqReceiver()
        msg = receiver.receive()

        assert msg.payload == {"nested": {"data": [1, 2, 3]}}

    @patch('zmq_client.Receiver')
    @patch('zmq_client.OmnibusCommunicator')
    def test_receive_with_list_payload(self, mock_communicator, mock_receiver_class):
        """Verify list payloads are handled correctly."""
        mock_omnibus_msg = Mock()
        mock_omnibus_msg.channel = "test"
        mock_omnibus_msg.timestamp = 100.0
        mock_omnibus_msg.payload = [1, 2, 3, "four", 5.0]

        mock_receiver_instance = Mock()
        mock_receiver_instance.recv_message.return_value = mock_omnibus_msg
        mock_receiver_class.return_value = mock_receiver_instance

        receiver = ZmqReceiver()
        msg = receiver.receive()

        assert msg.payload == [1, 2, 3, "four", 5.0]

    @patch('zmq_client.Receiver')
    @patch('zmq_client.OmnibusCommunicator')
    def test_receive_with_none_payload(self, mock_communicator, mock_receiver_class):
        """Verify None payloads are handled correctly."""
        mock_omnibus_msg = Mock()
        mock_omnibus_msg.channel = "test"
        mock_omnibus_msg.timestamp = 100.0
        mock_omnibus_msg.payload = None

        mock_receiver_instance = Mock()
        mock_receiver_instance.recv_message.return_value = mock_omnibus_msg
        mock_receiver_class.return_value = mock_receiver_instance

        receiver = ZmqReceiver()
        msg = receiver.receive()

        assert msg.payload is None
