from omnibus import Sender
import time

sender = Sender()
CHANNEL = "CAN/Parsley"

while True:
    fake_log_message = {
        "msg_type": "GENERAL_BOARD_STATUS",
        "board_id": "LOGGER",
        "data": {
            "time": time.time(),
            "status": "E_LOGGING"
        }
    }
    sender.send(CHANNEL, fake_log_message)
    time.sleep(0.01)
