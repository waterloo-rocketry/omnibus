from flask import Flask, render_template, request
from flask_socketio import SocketIO
from omnibus import Message as OmnibusMessage
from omnibus import Sender

app = Flask(__name__)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    serializer="msgpack",
    logger=False,
    engineio_logger=False,
)

# Lazily init on first so the WebSocket server can start accepting connections even without zmq running
_omnibus_sender: Sender | None = None

# SID of the bridge client, so we know which messages from zero_mq and which aren't
_bridge_sid: str | None = None

def get_omnibus_sender() -> Sender:
    # Creates the sender
    global _omnibus_sender
    if _omnibus_sender is None:
        _omnibus_sender = Sender()
    return _omnibus_sender

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("connect")  
def handle_connect(auth):
    # handles client connection including brige
    global _bridge_sid
    if isinstance(auth, dict) and auth.get("role") == "bridge":
        _bridge_sid = request.sid
        print(f">>> Bridge connected: {request.sid}")
    else:
        print(f">>> Client connected: {request.sid}")

@socketio.on("*")
def handle_channel_message(event, data):
    # Relay all channel messages between ZMQ and WS clients.
    # Messages from the bridge sent to WS clients with skip_sid so the bridge does not receive
    # Messages from WS clients, broadcast to everyone including the sender, Omnibus ZMQ so ZMQ subscribers receive them, tell the bridge to ignore it
    
    if request.sid == _bridge_sid: # ZMQ-originated, emit to all
        socketio.emit(event, data, skip_sid=request.sid)
    else: # WS-client-originated: emit to all and tell bridge to ignore it
        socketio.emit(event, data)
        if isinstance(data, list) and len(data) >= 2:
            get_omnibus_sender().send_message(OmnibusMessage(event, data[0], data[1]))

@socketio.on("disconnect")
def handle_disconnect():
    # Handles client disconnection including bridge
    global _bridge_sid
    if request.sid == _bridge_sid:
        _bridge_sid = None
        print(f">>> Bridge disconnected: {request.sid}")
    else:
        print(f">>> Client disconnected: {request.sid}")

if __name__ == "__main__":  # pragma: no cover
    print(">>> Starting SocketIO server on http://127.0.0.1:6767")
    socketio.run(app, host="127.0.0.1", port=6767)
