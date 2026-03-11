import argparse
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

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("connect")  
def handle_connect(auth):
    # handles client connection including bridge
    if isinstance(auth, dict) and auth.get("role") == "bridge":
        state.bridge_sid = request.sid
        print(f">>> Bridge connected: {request.sid}")
    else:
        print(f">>> Client connected: {request.sid}")

@socketio.on("*")
def handle_channel_message(event, data):
    # Relay all channel messages between ZMQ and WS clients.
    # Messages from the bridge are broadcast to all WS clients except the bridge itself (include_self=False)
    # Messages from WS clients, broadcast to everyone including the sender, Omnibus ZMQ so ZMQ subscribers receive them, tell the bridge to ignore it
    
    if request.sid == state.bridge_sid: # ZMQ-originated, emit to all
        emit(event, data, broadcast=True, include_self=False)
    else: # WS-client-originated: emit to all and tell bridge to ignore it
        emit(event, data, broadcast=True)
        if isinstance(data, list) and len(data) == 2:
            Sender().send_message(OmnibusMessage(event + WS_ORIGINATED_SUFFIX, data[0], data[1]))
        else:
            app.logger.warning("Dropping malformed WS payload for event '%s': %r", event, data)

@socketio.on("disconnect")
def handle_disconnect():
    # Handles client disconnection including bridge
    if request.sid == state.bridge_sid:
        state.bridge_sid = None
        print(f">>> Bridge disconnected: {request.sid}")
    else:
        print(f">>> Client disconnected: {request.sid}")

if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser(description="WebSocket server for Omnibus bridge")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=6767, help="Port to listen on (default: 6767)")
    args = parser.parse_args()
    print(f">>> Starting SocketIO server on {args.host}:{args.port}")
    socketio.run(app, host=args.host, port=args.port)
