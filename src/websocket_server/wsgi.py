from omnibus import Sender
from websocket_server.server import app, start_relay_sender

def _bootstrap() -> None:
    _ = Sender()  # Trigger auto discovery for Omnibus.
    start_relay_sender()

_bootstrap()
application = app