"""
Message translation between ZeroMQ and WebSocket formats.

ZeroMQ format: 3-part multipart message
    [channel_bytes, msgpack(timestamp), msgpack(payload)]

WebSocket format: msgpack-encoded list
    msgpack([channel, (timestamp, payload)])
"""

from dataclasses import dataclass
from typing import Any

import msgpack


@dataclass(frozen=True)
class Message:
    """
    Represents an Omnibus message.
    
    This is a local copy to avoid tight coupling with the omnibus library,
    though the structure is intentionally identical.
    """
    channel: str
    timestamp: float
    payload: Any


def zmq_to_message(frames: list[bytes]) -> Message:
    """
    Convert a 3-part ZeroMQ multipart message to a Message object.
    
    Args:
        frames: List of 3 byte frames [channel, timestamp, payload]
        
    Returns:
        Message object with decoded fields
        
    Raises:
        ValueError: If frames doesn't contain exactly 3 parts
    """
    if len(frames) != 3:
        raise ValueError(f"Expected 3 frames, got {len(frames)}")
    
    channel = frames[0].decode("utf-8")
    timestamp = msgpack.unpackb(frames[1])
    payload = msgpack.unpackb(frames[2])
    
    return Message(channel=channel, timestamp=timestamp, payload=payload)


def message_to_zmq(message: Message) -> list[bytes]:
    """
    Convert a Message object to a 3-part ZeroMQ multipart message.
    
    Args:
        message: Message object to convert
        
    Returns:
        List of 3 byte frames [channel, timestamp, payload]
    """
    return [
        message.channel.encode("utf-8"),
        msgpack.packb(message.timestamp),
        msgpack.packb(message.payload),
    ]


def message_to_websocket(message: Message) -> bytes:
    """
    Convert a Message object to WebSocket format.
    
    Args:
        message: Message object to convert
        
    Returns:
        msgpack-encoded bytes in format [channel, (timestamp, payload)]
    """
    return msgpack.packb([message.channel, (message.timestamp, message.payload)])


def websocket_to_message(data: bytes) -> Message:
    """
    Convert WebSocket format data to a Message object.
    
    Args:
        data: msgpack-encoded bytes in format [channel, (timestamp, payload)]
        
    Returns:
        Message object with decoded fields
        
    Raises:
        ValueError: If data doesn't match expected format
    """
    decoded = msgpack.unpackb(data)
    
    if not isinstance(decoded, list) or len(decoded) != 2:
        raise ValueError(f"Expected [channel, (timestamp, payload)], got {decoded}")
    
    channel = decoded[0]
    timestamp_payload = decoded[1]
    
    if not isinstance(timestamp_payload, (list, tuple)) or len(timestamp_payload) != 2:
        raise ValueError(f"Expected (timestamp, payload), got {timestamp_payload}")
    
    timestamp, payload = timestamp_payload
    
    return Message(channel=channel, timestamp=timestamp, payload=payload)


# Convenience functions for direct conversion

def zmq_to_websocket(frames: list[bytes]) -> bytes:
    """Convert ZeroMQ frames directly to WebSocket format."""
    return message_to_websocket(zmq_to_message(frames))


def websocket_to_zmq(data: bytes) -> list[bytes]:
    """Convert WebSocket format directly to ZeroMQ frames."""
    return message_to_zmq(websocket_to_message(data))
