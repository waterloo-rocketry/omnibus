from omnibus import Sender
from server import app, start_relay_sender

_ = Sender()  # Trigger auto discovery and cache the server IP for the relay sender thread.
start_relay_sender()

application = app
