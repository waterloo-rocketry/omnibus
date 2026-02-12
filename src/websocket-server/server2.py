import os
import socketio
from aiohttp import web
from omnibus import Message as OmnibusMessage
from omnibus import Sender

# python-socketio async server with native msgpack serialization
sio = socketio.AsyncServer(
    cors_allowed_origins="*",
    serializer="msgpack",
    logger=False,
    engineio_logger=False,
)

# Serve the test HTML page
here = os.path.dirname(os.path.abspath(__file__))
aiohttp_app = web.Application()
sio.attach(aiohttp_app)

# Omnibus sender for forwarding messages to ZeroMQ
omnibus_sender = Sender()

async def index(request):
    return web.FileResponse(os.path.join(here, "templates", "index.html"))

aiohttp_app.router.add_get("/", index)

@sio.on("connect")  # type: ignore[misc]
async def handle_connect(sid, environ, auth):
    """Handle client connection."""
    print(f">>> Client connected: {sid}")

@sio.on("*")  # type: ignore[misc]
async def handle_channel_message(event, sid, data):
    """
    Gets all channel messages and then sends
    Rebroadcast to all other clients on the same channel/event.
    """
    await sio.emit(event, data, skip_sid=sid)

@sio.on("publish")  # type: ignore[misc]
async def handle_publish(sid, data):
    """
    Receive message from client, forward to Omnibus, and broadcast to clients.
    """
    channel = data[0]
    timestamp, payload = data[1]

    # Forward to Omnibus ZeroMQ backend
    omnibus_sender.send_message(OmnibusMessage(channel, timestamp, payload))

    # Broadcast to channel-specific listeners
    await sio.emit(channel, [timestamp, payload], skip_sid=sid)

@sio.on("disconnect")  # type: ignore[misc]
async def handle_disconnect(sid):
    """Handle client disconnection."""
    print(f">>> Client disconnected: {sid}")

if __name__ == "__main__":
    print(">>> Starting SocketIO server on http://127.0.0.1:6767")
    web.run_app(aiohttp_app, host="127.0.0.1", port=6767)
