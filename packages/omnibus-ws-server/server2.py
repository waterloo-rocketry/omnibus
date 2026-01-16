import os
import time
from dataclasses import dataclass, asdict
from typing import Any

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

print(">>> server2.py imported")


socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="eventlet",
    logger=True,
    engineio_logger=True,
)


@dataclass
class Message:
    channel: str
    timestamp: float
    payload: Any


def create_app():
    here = os.path.dirname(os.path.abspath(__file__))
    app = Flask(__name__, template_folder=os.path.join(here, "templates"))
    app.config["SECRET_KEY"] = "secret"
    socketio.init_app(app)

    @app.route("/")
    def index():
        return render_template("index.html")

    @socketio.on("connect")
    def connect():
        print(">>> client connected")
        msg = Message("test_channel", time.time(), {"hello": "world"})
        emit("omnibus_message", asdict(msg))

    @socketio.on("disconnect")
    def disconnect():
        print(">>> client disconnected")

    return app


if __name__ == "__main__":
    print(">>> starting socketio.run on 0.0.0.0:8080")
    app = create_app()
    socketio.run(app, host="0.0.0.0", port=8080)
