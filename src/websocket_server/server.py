import queue
import threading
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from omnibus import Message as OmnibusMessage
from omnibus import Receiver
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

_zmq_outbound_queue: queue.Queue[OmnibusMessage] = queue.Queue()
_ws_broadcast_queue: queue.Queue[OmnibusMessage] = queue.Queue()
_workers_started = False
_workers_lock = threading.Lock()


def send_messages_to_omnibus(
    sender: Sender, relay_queue: queue.Queue[OmnibusMessage]
) -> None:
    while True:
        sender.send_message(relay_queue.get())


def queue_messages_for_websocket(
    receiver: Receiver, broadcast_queue: queue.Queue[OmnibusMessage]
) -> None:
    while True:
        msg = receiver.recv_message(None)
        if msg is None:
            continue

        if msg.channel.endswith(WS_ORIGINATED_SUFFIX):
            print(
                f"[websocket_server] skipping message on '{msg.channel}' "
                + "(originated from WS client)"
            )
            continue

        broadcast_queue.put(msg)


def broadcast_messages_to_websocket(
    broadcast_queue: queue.Queue[OmnibusMessage],
) -> None:
    while True:
        msg = broadcast_queue.get()
        socketio.emit(msg.channel, (msg.timestamp, msg.payload))


def _run_zmq_sender() -> None:
    send_messages_to_omnibus(Sender(), _zmq_outbound_queue)


def _run_zmq_receiver() -> None:
    queue_messages_for_websocket(Receiver(""), _ws_broadcast_queue)


def _run_websocket_broadcaster() -> None:
    broadcast_messages_to_websocket(_ws_broadcast_queue)


def _start_worker(name: str, target) -> None:
    thread = threading.Thread(name=name, target=target, daemon=True)
    thread.start()


def start_background_workers() -> None:
    global _workers_started

    with _workers_lock:
        if _workers_started:
            return

        _start_worker("ws-zmq-sender", _run_zmq_sender)
        _start_worker("ws-zmq-receiver", _run_zmq_receiver)
        _start_worker("ws-broadcast", _run_websocket_broadcaster)
        _workers_started = True

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("connect")
def handle_connect(auth: object):
    print(f">>> Client connected: {request.sid}")

@socketio.on("*")
def handle_channel_message(event: str, *args: object):
    if len(args) != 2:
        print(
            f">>> Malformed message on '{event}': expected 2 data args "
            + f"(timestamp, payload), got {len(args)}"
        )
        return

    timestamp, payload = args

    emit(event, (timestamp, payload), broadcast=True)
    _zmq_outbound_queue.put(
        OmnibusMessage(event + WS_ORIGINATED_SUFFIX, timestamp, payload)
    )

@socketio.on("disconnect")
def handle_disconnect():
    print(f">>> Client disconnected: {request.sid}")
