import os
import time
from dataclasses import dataclass, asdict
from typing import Any

import zmq
import msgpack

from flask import Flask, render_template
from flask_socketio import SocketIO, emit



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




def parse_client_message(data):
    
    channel = data.get("channel","")
    timestamp = data.get("timestamp", 0.0)
    payload = data.get("payload", "")

    
    return Message(channel, timestamp, payload)



# NEED TO FIX THIS ==> ENDPOINT

def forward_to_omnibus(msg: Message) -> None:
    packed = msgpack.packb(
        [msg.channel, msg.timestamp, msg.payload],
        use_bin_type=True
    )
    endpoint.send(packed)        # define endpoint func



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

    @socketio.on("publish")
    def publish_data(data):

        msg = parse_client_message(data)
        forward = forward_to_omnibus(msg)     # currently returning None since no return
        emit("omnibus", {"forward": bool(forward), "channel": msg.channel})

        

    @socketio.on("disconnect")
    def disconnect():
        print(">>> client disconnected")

    return app


if __name__ == "__main__":
    print(">>> starting socketio.run on 0.0.0.0:8080")
    app = create_app()
    socketio.run(app, host="0.0.0.0", port=8080)





# Previous Test Code

# >>> import socketio
# >>> 
# >>> sio = socketio.Client()
# >>>
# >>> @sio.event
# ... def connect():
# ...     print("CLIENT: connected")
# >>>
# >>> @sio.event
# ... def connect():
# ...     print("CLIENT: connected")
# ...     print("CLIENT: connected")
# ...
# >>> @sio.on("omnibus_message")
# ... def on_msg(data):
# ...     print("CLIENT got omnibus_message:")    
# ...     print(data)
# ...
# >>> @sio.event
# ... def disconnect():
# ...     print("CLIENT: disconnected")
# ...
# >>> sio.connect("http://localhost:8080")