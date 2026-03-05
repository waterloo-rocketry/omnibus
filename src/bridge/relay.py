import time
from collections import deque
import socketio
from omnibus import Receiver
from socketio import exceptions

WS_URL = "http://127.0.0.1:6767"
BRIDGE_AUTH = {"role": "bridge"}

def connect_with_retry(sio: socketio.Client) -> None:
    # Attemps to recconnect to the WS server if it disconnects
    while True:
        try:
            sio.connect(WS_URL, auth=BRIDGE_AUTH)
            print(f">>> Connected to WebSocket server at {WS_URL}")
            return
        except exceptions.ConnectionError:
            print(f">>> Waiting for WebSocket server at {WS_URL}...")
            time.sleep(1)

def reconnect(sio: socketio.Client) -> None:
    # Clean up brokwn connection and attempt to reconnect
    print(">>> WebSocket server connection lost, reconnecting...")
    try:
        sio.disconnect()
    except Exception:
        pass
    connect_with_retry(sio)

def main():
    print("Starting bridge relay loop...")

    sio = socketio.Client(
        logger=False,
        engineio_logger=False,
        serializer="msgpack",
        reconnection=False,  # Manually manage reconnection
    )

    # Bounded deque of (channel, timestamp) pairs that the WS server has already broadcast to web clients.  The bridge uses this to skip re-broadcasting messages
    _ws_originated: deque[tuple[str, float]] = deque(maxlen=256)

    @sio.on("*")  # type: ignore[misc]
    def on_ws_broadcast(event: str, data: list) -> None:
        # When the websocket server sends a message to clients this fires first
        # Adds message to deque so that when the message is relayed back from ZMQ, the bridge can skip it to avoid duplicates
        # If not skipped the message would be broadcast to clients twice, once from the WS server and once from the bridge when it relays back to clients
        
        if isinstance(data, list) and len(data) >= 1:
            _ws_originated.append((event, data[0]))

    connect_with_retry(sio)

    # Subscribe to all Omnibus channels
    receiver = Receiver("")

    while True:
        msg = receiver.recv_message(None)

        if msg is None:
            continue

        # Reconnect if server2 went down
        if not sio.connected:
            reconnect(sio)

        # Skip messages that the WS server already broadcast to clients
        # Re-emitting them would cause duplicate delivery
        key = (msg.channel, msg.timestamp)
        if key in _ws_originated:
            _ws_originated.remove(key)
            print(f"[bridge] skipping WS-originated message on '{msg.channel}'")
            continue

        try:
            sio.emit(msg.channel, [msg.timestamp, msg.payload])
            print(f"[bridge] relayed '{msg.channel}'")
        except Exception:
            # Server dropped
            reconnect(sio)

if __name__ == "__main__":  # pragma: no cover
    main()
