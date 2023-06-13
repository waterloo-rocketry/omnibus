import time

from omnibus import Sender

sender = Sender()


def send_actuator(actuator, state: bool):
    message = {"data": {
        "time": time.time(),
        "can_msg": {
            "msg_type": "ACTUATOR_CMD",
            "board_id": "ANY",
            "time": 0,
            "actuator": actuator,
            "req_state": 'ACTUATOR_ON' if state else 'ACTUATOR_OFF'
        }
    }}
    sender.send("CAN/Commands", message)


def command(state):
    if "Injector Valve Command" in state:
        if state["Injector Valve Command"] == "OPEN":
            send_actuator("ACTUATOR_INJECTOR_VALVE", True)
        if state["Injector Valve Command"] == "CLOSED":
            send_actuator("ACTUATOR_INJECTOR_VALVE", False)
    if "Vent Valve Command" in state:
        if state["Vent Valve Command"] == "OPEN":
            send_actuator("ACTUATOR_VENT_VALVE", False)
        if state["Vent Valve Command"] == "CLOSED":
            send_actuator("ACTUATOR_VENT_VALVE", True)
