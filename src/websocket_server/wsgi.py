import os

from omnibus import Sender
from server import app, start_relay_sender

_ = Sender(server_ip=_omnibus_server_host)
start_relay_sender()

application = app
