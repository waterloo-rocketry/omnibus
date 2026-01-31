import os
import time
from dataclasses import dataclass, asdict
from typing import Any

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from omnibus import Message as OmnibusMessage
from omnibus import Sender, Receiver



socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="eventlet",
    logger=True,
    engineio_logger=True,
)

#only when it recievs a post request to /send-legacy-omnibus-information as opposed to always sending
def create_app():
    here = os.path.dirname(os.path.abspath(__file__))
    app = Flask(__name__, template_folder=os.path.join(here, "templates"))
    app.config["SECRET_KEY"] = "secret"
    socketio.init_app(app)
    da_sender = Sender()
    da_receiver = Receiver("")

    def parse_client_message(data):
        channel = data.get("channel", "")
        timestamp = data.get("timestamp", 0.0)
        payload = data.get("payload", "")
        return OmnibusMessage(channel, timestamp, payload)

    def forward_to_omnibus(msg: OmnibusMessage) -> None:
        da_sender.send(msg)

    @app.route("/")
    def index():
        return render_template("index.html")
    
    @app.route("/send-legacy-omnibus-information", methods=["POST"])
    def send_legacy_omnibus_information():
        data = request.get_json()
        print(f"Received POST: {data}")
        socketio.emit("omnibus_message", data)
        return "OK"

    @socketio.on("connect")
    def connect():
        
        print(">>> client connected")
        msg = OmnibusMessage("test_channel", time.time(), {"hello": "world"})
        emit("omnibus_message", asdict(msg))
        

    @socketio.on("publish")
    def publish_data(data):

        msg = parse_client_message(data)
        forward_to_omnibus(msg)
        emit("omnibus", {"forward": True, "channel": msg.channel})

        

    @socketio.on("disconnect")
    def disconnect():
        print(">>> client disconnected")

    return app


if __name__ == "__main__":
    print(">>> starting socketio.run on 0.0.0.0:8080")
    app = create_app()
    socketio.run(app, host="0.0.0.0", port=8080, debug=True)
