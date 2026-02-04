"""
This is a ZeroMQ client that receives message from the Omnibus server

Returns a multi-part ZeroMQ message and converts it to a local Message object.
For now, the server IP is hard-coded, this is only for the prototype.
"""

from omnibus import Receiver
from omnibus.omnibus import OmnibusCommunicator

from .translator import Message, zmq_to_message

# Hardcoded for prototype - skip auto-discovery
DEFAULT_SERVER_IP = "127.0.0.1"

class ZmqReceiver:
    """
    Receives messages from the Omnibus server.
    
    Wraps omnibus.Receiver and converts messages to our Message format.
    """
    
    def __init__(self, server_ip: str = DEFAULT_SERVER_IP, channels: tuple[str, ...] = ("",)):
        """
        Initalizes the ZeroMQ receiver.

        Takes in the server IP (hardcoded for now) and optional channels to subscribe to.
        Returns Message object in multipart ZeroMQ format.
        Args:
            server_ip: IP address of the Omnibus server.
            channels: Tuple of channel strings to subscribe to. Subscribes to all channels by default. ("")
        """
        # Skip auto-discovery (for now) by setting the server IP directly
        OmnibusCommunicator.server_ip = server_ip
        
        self._channels = channels
        self._receiver = Receiver(*channels)
    
    def receive(self, timeout_ms: int | None = 100) -> Message | None:
        """
        Receive a message from Omnibus.
        
        Args:
            timeout_ms: Timeout in milliseconds. None blocks forever.
                        Default 100ms to allow periodic checking.
        
        Returns:
            Message if one was received, None if timeout.
        """
        omnibus_msg = self._receiver.recv_message(timeout=timeout_ms)
        
        if omnibus_msg is None:
            return None
        
        # Convert to our Message type
        return Message(
            channel=omnibus_msg.channel,
            timestamp=omnibus_msg.timestamp,
            payload=omnibus_msg.payload,
        )
