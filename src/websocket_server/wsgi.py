from omnibus import Sender
from server import app

_ = Sender()  # Trigger auto discovery and cache the server IP for the relay sender thread.

application = app
