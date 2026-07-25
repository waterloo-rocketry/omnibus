import os

from omnibus import Sender
from server import app, start_relay_sender

_omnibus_server_host = os.environ.get("OMNIBUS_SERVER_HOST") or None

_ = Sender(server_ip=_omnibus_server_host)
start_relay_sender()

application = app
