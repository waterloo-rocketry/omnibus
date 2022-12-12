from omnibus import Sender
import time

sender = Sender()
CHANNEL = "CAN/Parsley"

while True:
<<<<<<< HEAD
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
=======
	fake_log_message = {
		"msg_type":"GENERAL_BOARD_STATUS",
		"board_id":"LOGGER",
		"data": {
			"time": time.time(),
			"status":"E_LOGGING"
		}
	}
	sender.send(CHANNEL, fake_log_message)
	time.sleep(0.01)
>>>>>>> 5deeacd1d7231b65e2c44e7d6af0795a613186b5
