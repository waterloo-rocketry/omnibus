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

# Omnibus sender for forwarding messages to ZeroMQ
omnibus_sender = Sender()

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("connect")  # type: ignore[misc]
def handle_connect(auth):
    """Handle client connection."""
    print(f">>> Client connected: {request.sid}")

@socketio.on("*")  # type: ignore[misc]
def handle_channel_message(event, data):
    """
    Gets all channel messages and then sends
    Rebroadcast to all other clients on the same channel/event.
    """
    socketio.emit(event, data, skip_sid=request.sid)

@socketio.on("publish")  # type: ignore[misc]
def handle_publish(data):
    """
    Receive message from client, forward to Omnibus, and broadcast to clients.
    """
    channel = data[0]
    timestamp, payload = data[1]

    # Forward to Omnibus ZeroMQ backend
    omnibus_sender.send_message(OmnibusMessage(channel, timestamp, payload))

    # Broadcast to channel-specific listeners
    socketio.emit(channel, [timestamp, payload], skip_sid=request.sid)

@socketio.on("disconnect")  # type: ignore[misc]
def handle_disconnect():
    """Handle client disconnection."""
    print(f">>> Client disconnected: {request.sid}")

if __name__ == "__main__":
    print(">>> Starting SocketIO server on http://127.0.0.1:6767")
    socketio.run(app, host="127.0.0.1", port=6767)
