import time
from omnibus import Sender
sender = Sender()


def send_actuator(actuator: str, state: bool):
    message = {
        "parsley": "ALL",
        "data": {
            "time": time.time(),
            "can_msg": {
                "msg_type": "ACTUATOR_CMD",
                "board_id": "ANY",
                "time": 0,
                "actuator": actuator,
                "req_state": 'ACTUATOR_ON' if state else 'ACTUATOR_OFF'
            }
        }
    }
    sender.send("CAN/Commands", message)


def command(state: dict[str, str | int | float]):
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
    if "Fill Dump Valve Command" in state:
        if state["Fill Dump Valve Command"] == "OPEN":
            send_actuator("ACTUATOR_FILL_DUMP_VALVE", False)
        if state["Fill Dump Valve Command"] == "CLOSED":
            send_actuator("ACTUATOR_FILL_DUMP_VALVE", True)
