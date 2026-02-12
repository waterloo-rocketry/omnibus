#use socketio not flask socketio to get msgpack working and the channels
import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from omnibus import Message as OmnibusMessage
from omnibus import Sender
import msgpack

# Flask-SocketIO server configuration
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="eventlet",
    logger=False,
    engineio_logger=False
)

def create_app():
    """Create and configure the Flask-SocketIO application."""
    here = os.path.dirname(os.path.abspath(__file__))
    app = Flask(__name__, template_folder=os.path.join(here, "templates"))
    app.config["SECRET_KEY"] = "secret"
    socketio.init_app(app)

    # Omnibus sender for forwarding messages to ZeroMQ
    omnibus_sender = Sender()

    def get_msgpack_data(data) -> OmnibusMessage | None:
        """Decode msgpack binary"""
        decoded = msgpack.unpackb(data, raw=False)
        
        msg = parse_client_message(decoded)
        return msg

    def parse_client_message(data) -> OmnibusMessage | None:
        """
        Parse incoming WebSocket message.
        Expected format: [channel, [timestamp, payload]]
        Returns: OmnibusMessage or None if invalid
        """
        if not isinstance(data, list) or len(data) != 2:
            print(">>> Invalid message format from client")
            return None
        
        channel = data[0]
        ts_payload = data[1]
        
        if not isinstance(ts_payload, list) or len(ts_payload) != 2:
            print(">>> Invalid message format from client")
            return None
        
        timestamp, payload = ts_payload
        return OmnibusMessage(channel, timestamp, payload)

    @app.route("/")
    def index():
        """Serve the test client HTML page."""
        return render_template("index.html")

    @socketio.on("connect")
    def handle_connect() -> None:
        """Handle client connection."""
        print(">>> Client connected")

    @socketio.on("omnibus_message") #on any
    def handle_omnibus_message(data) -> None:
        """
        Receive omnibus_message from bridge and rebroadcast to all web clients.
        This is the main relay point for Omnibus → WebSocket flow.
        Bridge sends msgpack-encoded: [channel, [timestamp, payload]]
        """
        # Decode msgpack from bridge
        msg = get_msgpack_data(data)
        if msg is None:
            print(">>> Invalid message format from bridge")
            return
        
        # Re-encode as msgpack and broadcast to all web clients
        packed = msgpack.packb([msg.channel, [msg.timestamp, msg.payload]])
        emit(msg.channel, packed, broadcast=True, include_self=False)

    @socketio.on("publish")
    def handle_publish(data) -> None:
        """
        Receive message from client, forward to Omnibus, and broadcast to clients.
        Client sends msgpack-encoded: [channel, [timestamp, payload]]
        """
        # Decode msgpack from browser
        msg = get_msgpack_data(data)
        if msg is None:
            print(">>> Invalid message format from client")
            return
        
        # Forward to Omnibus ZeroMQ Backend (uses msgpack internally)
        omnibus_sender.send_message(msg)
        
        # Broadcast msgpack to channel-specific listeners in case was meant to go to a seperate web client instance
        packed = msgpack.packb([msg.channel, [msg.timestamp, msg.payload]])
        emit(msg.channel, packed, broadcast=True, include_self=False)

    @socketio.on("disconnect")
    def handle_disconnect() -> None:
        """Handle client disconnection."""
        print(">>> Client disconnected")

    return app

if __name__ == "__main__":
    app = create_app()
    print(">>> Starting SocketIO server on http://127.0.0.1:6767")
    socketio.run(app, host="127.0.0.1", port=6767, debug=True, use_reloader=True)