import os
import time
from dataclasses import dataclass, asdict
from typing import Any

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from omnibus import Message as OmnibusMessage
from omnibus import Sender, Receiver

print(">>> server2.py imported")


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

    @app.route("/")
    def index():
        return render_template("index.html")
    
    @app.route("/send-legacy-omnibus-information", methods=["POST"])
    def get_legacy_omnibus_information():
        #translate from legacy omnibus endpoint to websocket message
        message = da_receiver.recv()
        print(f">>> received legacy omnibus message: {message}")
        msg = OmnibusMessage("peepep", time.time(), {"data": message})
        emit("omnibus_message", asdict(msg))
        
        print(f">>> emitting websocket message: {msg}")
        return render_template("index.html")

    @socketio.on("connect")
    def connect():
        get_legacy_omnibus_information()
        
        '''
        print(">>> client connected")
        msg = OmnibusMessage("test_channel", time.time(), {"hello": "world"})
        emit("omnibus_message", asdict(msg))
        '''

    @socketio.on("disconnect")
    def disconnect():
        print(">>> client disconnected")

    return app


if __name__ == "__main__":
    print(">>> starting socketio.run on 0.0.0.0:8080")
    app = create_app()
    socketio.run(app, host="0.0.0.0", port=8080, debug=True)
