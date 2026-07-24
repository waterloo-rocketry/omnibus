import time
from omnibus import Sender
sender = Sender()


def send_actuator(actuator: str, state: bool):
    message = {
        "parsley": "EGSE-UPPER/usb//dev/ttyACM0",
        "data": {
            "time": time.time(),
            "can_msg": {
                'msg_prio': 'HIGHEST',
                'msg_type': 'ACTUATOR_CMD',
                'board_type_id': 'DAQ',
                'board_inst_id': 'GROUND',
                "time": 0,
                "msg_metadata": actuator,
                "cmd_state": 'ACT_STATE_ON' if state else 'ACT_STATE_OFF'
            }
        }
    }
    sender.send("CAN/Commands", message)


def command(state: dict[str, str | int | float]):
    if "QD301 Command" in state:
        if state["QD301 Command"] == "OPEN":
            send_actuator("ACTUATOR_OX_INJECTOR_VALVE", True)
        if state["QD301 Command"] == "CLOSED":
            send_actuator("ACTUATOR_OX_INJECTOR_VALVE", False)
    if "Ignition Primary Command" in state:
        if state["Ignition Primary Command"] == "OPEN":
            send_actuator("ACTUATOR_IGNITION", True)
        if state["Ignition Primary Command"] == "CLOSED":
            send_actuator("ACTUATOR_IGNITION", False)
