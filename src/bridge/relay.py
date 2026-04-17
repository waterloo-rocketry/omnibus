import time
import socketio
from omnibus import Receiver
from socketio import exceptions
from omnibus import WS_ORIGINATED_SUFFIX

BRIDGE_AUTH = {"role": "bridge"}

def connect_with_retry(sio: socketio.Client, ws_url: str) -> None:
    # Attempts to reconnect to the WS server if it disconnects
    while True:
        try:
            sio.connect(ws_url, auth=BRIDGE_AUTH)
            print(f">>> Connected to WebSocket server at {ws_url}")
            return
        except exceptions.ConnectionError:
            print(f">>> Waiting for WebSocket server at {ws_url}...")
            time.sleep(1)

def reconnect(sio: socketio.Client, ws_url: str) -> None:
    # Clean up broken connection and attempt to reconnect
    print(">>> WebSocket server connection lost, reconnecting...")
    try:
        sio.disconnect()
    except Exception as e:
        print(f"Error disconnecting from WS server: {e}")
    connect_with_retry(sio, ws_url)

def main(ws_url: str = "http://127.0.0.1:6767") -> None:

    print("Starting bridge relay loop...")

    sio = socketio.Client(
        logger=False,
        engineio_logger=False,
        serializer="msgpack",
        reconnection=False,  # Manually manage reconnection
    )

    connect_with_retry(sio, ws_url)

    # Subscribe to all Omnibus channels
    receiver = Receiver("")

    while True:
        msg = receiver.recv_message(None)
        if msg is None:
            continue

        # Reconnect if WebSocket server went down
        if not sio.connected:
            reconnect(sio, ws_url)

        # Skip messages that originated from a WS client.
        # They already went into ZMQ with suffix appended, we don't re-broadcast.
        
        if msg.channel.endswith(WS_ORIGINATED_SUFFIX):
            print(f"[bridge] skipping message on '{msg.channel}' (originated from WS client)")
            continue

        payload = (msg.timestamp, msg.payload)
        try:
            sio.emit(msg.channel, payload) 
        except (exceptions.ConnectionError, exceptions.BadNamespaceError) as e:
            print(f">>> Error sending message to WS server: {e}")
            reconnect(sio, ws_url)
            try:
                sio.emit(msg.channel, payload) 
            except (exceptions.ConnectionError, exceptions.BadNamespaceError) as retry_error:
                print(f"Failed to relay {msg.channel} after reconnect, dropping frame: {retry_error}")
                continue
        except Exception as e: 
            print(f">>> Unexpected error: {e}")
            raise
