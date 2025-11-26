import time
from omnibus import Sender
sender = Sender()

from omnibus.message_types import RLCSv3Message

def send_actuator(actuator: str, state: bool):
    message = {
        "parsley": "DESKTOP-6LBH021/usb/COM8",
        "data": {
            "time": time.time(),
            "can_msg": {
                'msg_prio': 'HIGHEST',
                'msg_type': 'ACTUATOR_CMD',
                'board_type_id': 'DAQ',
                'board_inst_id': 'GROUND',
                "time": 0,
                "actuator": actuator,
                "cmd_state": 'ACT_STATE_ON' if state else 'ACT_STATE_OFF'
            }
        }
    }
    sender.send("CAN/Commands", message)


def command(state: RLCSv3Message):
    if "QD301 Command" in state.data:
        if state.data["QD301 Command"] == "OPEN":
            send_actuator("ACTUATOR_OX_INJECTOR_VALVE", True)
        if state.data["QD301 Command"] == "CLOSED":
            send_actuator("ACTUATOR_OX_INJECTOR_VALVE", False)
