"""
Omnibus Bridge - WebSocket bridge for the Omnibus messaging system.

This package provides a bidirectional bridge between ZeroMQ (Omnibus) 
and WebSocket, allowing web clients to participate in the Omnibus ecosystem.
"""

from .translator import Message, zmq_to_message, message_to_zmq, message_to_websocket, websocket_to_message
from .zmq_client import ZmqReceiver

__all__ = [
    "Message",
    "zmq_to_message",
    "message_to_zmq", 
    "message_to_websocket",
    "websocket_to_message",
    "ZmqReceiver",
]
