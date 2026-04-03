import queue
from dataclasses import dataclass
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from omnibus import Message as OmnibusMessage
from omnibus import Sender
from omnibus import WS_ORIGINATED_SUFFIX

app = Flask(__name__)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    serializer="msgpack",
    logger=False,
    engineio_logger=False,
)

@dataclass
class _State:
    bridge_sid: str | None = None

state = _State()

_relay_queue: queue.Queue[OmnibusMessage] = queue.Queue()

def start_relay_sender():
    """Start the persistent ZMQ sender background thread.

    Must be called after Omnibus auto-discovery so that the server IP
    is already cached in OmnibusCommunicator.
    """
    def _sender_loop():
        sender = Sender()
        while True:
            msg = _relay_queue.get()
            sender.send_message(msg)
    socketio.start_background_task(_sender_loop)

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("connect")  
def handle_connect(auth: object):
    # handles client connection including bridge
    if isinstance(auth, dict) and auth.get("role") == "bridge":
        if state.bridge_sid is not None:
            raise ConnectionRefusedError("Only one bridge connection allowed")
        state.bridge_sid = request.sid
        print(f">>> Bridge connected: {request.sid}")
    else:
        print(f">>> Client connected: {request.sid}")

@socketio.on("*")
def handle_channel_message(event: str, *args: tuple[float, object]):
    # Relay all channel messages between ZMQ and WS clients.
    # Messages must carry exactly two data args: (timestamp, payload).
    if len(args) != 2:
        print(f">>> Malformed message on '{event}': expected 2 data args (timestamp, payload), got {len(args)}")
        return
    timestamp, payload = args
    # Messages from the bridge are broadcast to all WS clients except the bridge itself (include_self=False)
    # Messages from WS clients, broadcast to everyone including the sender, Omnibus ZMQ so ZMQ subscribers receive them, tell the bridge to ignore it
    if request.sid == state.bridge_sid: # ZMQ-originated, emit to all
        emit(event, (timestamp, payload), broadcast=True, include_self=False)
    else: # WS-client-originated: emit to all and tell bridge to ignore it
        emit(event, (timestamp, payload), broadcast=True)
        _relay_queue.put(OmnibusMessage(event + WS_ORIGINATED_SUFFIX, timestamp, payload))

@socketio.on("disconnect")
def handle_disconnect():
    # Handles client disconnection including bridge
    if request.sid == state.bridge_sid:
        state.bridge_sid = None
        print(f">>> Bridge disconnected: {request.sid}")
    else:
        print(f">>> Client disconnected: {request.sid}")
