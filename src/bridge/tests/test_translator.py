"""Tests for message translation functions."""

import pytest
import msgpack

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from translator import (
    Message,
    zmq_to_message,
    message_to_zmq,
    message_to_websocket,
    websocket_to_message,
    zmq_to_websocket,
    websocket_to_zmq,
)


class TestMessage:
    """Tests for the Message dataclass."""
    
    def test_message_creation(self):
        msg = Message(channel="test", timestamp=123.456, payload={"key": "value"})
        assert msg.channel == "test"
        assert msg.timestamp == 123.456
        assert msg.payload == {"key": "value"}
    
    def test_message_is_frozen(self):
        msg = Message(channel="test", timestamp=123.456, payload={})
        with pytest.raises(AttributeError):
            msg.channel = "modified"  # type: ignore[misc]


class TestZmqToMessage:
    """Tests for ZeroMQ to Message conversion."""
    
    def test_basic_conversion(self):
        frames = [
            b"sensors/temperature",
            msgpack.packb(1737745200.123),
            msgpack.packb({"value": 25.5}),
        ]
        msg = zmq_to_message(frames)
        
        assert msg.channel == "sensors/temperature"
        assert msg.timestamp == 1737745200.123
        assert msg.payload == {"value": 25.5}
    
    def test_empty_payload(self):
        frames = [
            b"channel",
            msgpack.packb(100.0),
            msgpack.packb(None),
        ]
        msg = zmq_to_message(frames)
        assert msg.payload is None
    
    def test_list_payload(self):
        frames = [
            b"channel",
            msgpack.packb(100.0),
            msgpack.packb([1, 2, 3]),
        ]
        msg = zmq_to_message(frames)
        assert msg.payload == [1, 2, 3]
    
    def test_string_payload(self):
        frames = [
            b"channel",
            msgpack.packb(100.0),
            msgpack.packb("hello"),
        ]
        msg = zmq_to_message(frames)
        assert msg.payload == "hello"
    
    def test_wrong_frame_count_raises(self):
        with pytest.raises(ValueError, match="Expected 3 frames"):
            zmq_to_message([b"only_one"])
        
        with pytest.raises(ValueError, match="Expected 3 frames"):
            zmq_to_message([b"one", b"two"])


class TestMessageToZmq:
    """Tests for Message to ZeroMQ conversion."""
    
    def test_basic_conversion(self):
        msg = Message(
            channel="sensors/temperature",
            timestamp=1737745200.123,
            payload={"value": 25.5}
        )
        frames = message_to_zmq(msg)
        
        assert len(frames) == 3
        assert frames[0] == b"sensors/temperature"
        assert msgpack.unpackb(frames[1]) == 1737745200.123
        assert msgpack.unpackb(frames[2]) == {"value": 25.5}
    
    def test_unicode_channel(self):
        msg = Message(channel="données/température", timestamp=100.0, payload={})
        frames = message_to_zmq(msg)
        assert frames[0] == "données/température".encode("utf-8")


class TestMessageToWebsocket:
    """Tests for Message to WebSocket conversion."""
    
    def test_basic_conversion(self):
        msg = Message(
            channel="sensors/temperature",
            timestamp=1737745200.123,
            payload={"value": 25.5}
        )
        data = message_to_websocket(msg)
        
        decoded = msgpack.unpackb(data)
        assert decoded[0] == "sensors/temperature"
        assert decoded[1][0] == 1737745200.123
        assert decoded[1][1] == {"value": 25.5}
    
    def test_format_is_channel_tuple(self):
        """Verify the format is [channel, (timestamp, payload)]."""
        msg = Message(channel="ch", timestamp=1.0, payload="data")
        data = message_to_websocket(msg)
        decoded = msgpack.unpackb(data)
        
        assert isinstance(decoded, list)
        assert len(decoded) == 2
        assert isinstance(decoded[0], str)
        assert isinstance(decoded[1], (list, tuple))
        assert len(decoded[1]) == 2


class TestWebsocketToMessage:
    """Tests for WebSocket to Message conversion."""
    
    def test_basic_conversion(self):
        data = msgpack.packb(["sensors/temperature", (1737745200.123, {"value": 25.5})])
        msg = websocket_to_message(data)
        
        assert msg.channel == "sensors/temperature"
        assert msg.timestamp == 1737745200.123
        assert msg.payload == {"value": 25.5}
    
    def test_list_instead_of_tuple(self):
        """msgpack doesn't distinguish lists from tuples, both should work."""
        data = msgpack.packb(["channel", [100.0, "payload"]])
        msg = websocket_to_message(data)
        
        assert msg.channel == "channel"
        assert msg.timestamp == 100.0
        assert msg.payload == "payload"
    
    def test_invalid_format_raises(self):
        # Not a list
        with pytest.raises(ValueError):
            websocket_to_message(msgpack.packb("not a list"))
        
        # Wrong length
        with pytest.raises(ValueError):
            websocket_to_message(msgpack.packb(["only_channel"]))
        
        # Invalid timestamp_payload format
        with pytest.raises(ValueError):
            websocket_to_message(msgpack.packb(["channel", "not_a_tuple"]))


class TestRoundTrip:
    """Tests for round-trip conversions to ensure data integrity."""
    
    def test_zmq_to_ws_to_zmq(self):
        """ZMQ → Message → WebSocket → Message → ZMQ should preserve data."""
        original_frames = [
            b"test/channel",
            msgpack.packb(999.999),
            msgpack.packb({"nested": {"data": [1, 2, 3]}}),
        ]
        
        # Convert to WebSocket and back
        ws_data = zmq_to_websocket(original_frames)
        result_frames = websocket_to_zmq(ws_data)
        
        # Compare
        assert result_frames[0] == original_frames[0]
        assert msgpack.unpackb(result_frames[1]) == msgpack.unpackb(original_frames[1])
        assert msgpack.unpackb(result_frames[2]) == msgpack.unpackb(original_frames[2])
    
    def test_ws_to_zmq_to_ws(self):
        """WebSocket → Message → ZMQ → Message → WebSocket should preserve data."""
        original_data = msgpack.packb(["my/channel", (123.456, {"key": "value"})])
        
        # Convert to ZMQ and back
        frames = websocket_to_zmq(original_data)
        result_data = zmq_to_websocket(frames)
        
        # Compare decoded values
        assert msgpack.unpackb(result_data) == msgpack.unpackb(original_data)
    
    def test_various_payload_types(self):
        """Test round-trip with various payload types."""
        payloads = [
            None,
            True,
            False,
            42,
            3.14159,
            "string",
            [1, 2, 3],
            {"nested": {"dict": True}},
            [{"mixed": 1}, "types", None],
        ]
        
        for payload in payloads:
            msg = Message(channel="test", timestamp=100.0, payload=payload)
            
            # ZMQ round-trip
            frames = message_to_zmq(msg)
            recovered = zmq_to_message(frames)
            assert recovered.payload == payload, f"ZMQ round-trip failed for {payload}"
            
            # WebSocket round-trip
            ws_data = message_to_websocket(msg)
            recovered = websocket_to_message(ws_data)
            assert recovered.payload == payload, f"WebSocket round-trip failed for {payload}"
