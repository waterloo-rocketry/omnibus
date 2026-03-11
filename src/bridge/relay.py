import logging
import time
import socketio
from omnibus import Receiver
from socketio import exceptions
from omnibus import WS_ORIGINATED_SUFFIX

WS_URL = "http://127.0.0.1:6767"
BRIDGE_AUTH = {"role": "bridge"}

logger = logging.getLogger(__name__)

def connect_with_retry(sio: socketio.Client) -> None:
    # Attempts to reconnect to the WS server if it disconnects
    while True:
        try:
            sio.connect(WS_URL, auth=BRIDGE_AUTH)
            print(f">>> Connected to WebSocket server at {WS_URL}")
            return
        except exceptions.ConnectionError:
            print(f">>> Waiting for WebSocket server at {WS_URL}...")
            time.sleep(1)

def reconnect(sio: socketio.Client) -> None:
    # Clean up broken connection and attempt to reconnect
    print(">>> WebSocket server connection lost, reconnecting...")
    try:
        sio.disconnect()
    except Exception as e:
        logger.warning(f"Error disconnecting from WS server: {e}")
    connect_with_retry(sio)

def main() -> None:
    print("Starting bridge relay loop...")

    sio = socketio.Client(
        logger=False,
        engineio_logger=False,
        serializer="msgpack",
        reconnection=False,  # Manually manage reconnection
    )

    connect_with_retry(sio)

    # Subscribe to all Omnibus channels
    receiver = Receiver("")

    while True:
        msg = receiver.recv_message(None)

        # Reconnect if WebSocket server went down
        if not sio.connected:
            reconnect(sio)

        # Skip messages that originated from a WS client.
        # They already went into ZMQ with suffix appended, we don't re-broadcast.
        
        if msg.channel.endswith(WS_ORIGINATED_SUFFIX):
            print(f"[bridge] skipping message on '{msg.channel}' (originated from WS client)")
            continue

        payload = [msg.timestamp, msg.payload]
        try:
            sio.emit(msg.channel, payload) 
            print(f"[bridge] relayed '{msg.channel}'")
        except (exceptions.ConnectionError, exceptions.BadNamespaceError) as e:
            print(f">>> Error sending message to WS server: {e}")
            reconnect(sio)
            try:
                sio.emit(msg.channel, payload) 
                print(f"[bridge] relayed '{msg.channel}' after reconnecting")
            except (exceptions.ConnectionError, exceptions.BadNamespaceError) as retry_error:
                logger.error("Failed to relay %s after reconnect: %s", msg.channel, retry_error)
                continue
            print(f"[bridge] relayed '{msg.channel}' after reconnecting")
        except Exception as e: 
            print(f">>> Unexpected error: {e}")
            raise

        

if __name__ == "__main__":  # pragma: no cover
    main()
