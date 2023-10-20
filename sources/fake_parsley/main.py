from omnibus import Sender
import random
import time

sender = Sender()
CHANNEL = "CAN/Parsley"

fake_msgs = [
    {'board_id': 'CHARGING', 'msg_type': 'SENSOR_ANALOG', 'data': {
        'time': 0, 'sensor_id': 'SENSOR_BATT_CURR', 'value': 0}},
    {'board_id': 'CHARGING', 'msg_type': 'SENSOR_ANALOG', 'data': {
        'time': 0, 'sensor_id': 'SENSOR_BUS_CURR', 'value': 0}},
    {'board_id': 'CHARGING', 'msg_type': 'SENSOR_ANALOG', 'data': {
        'time': 0, 'sensor_id': 'SENSOR_CHARGE_CURR', 'value': 0}},
    {'board_id': 'CHARGING', 'msg_type': 'SENSOR_ANALOG', 'data': {
        'time': 0, 'sensor_id': 'SENSOR_BATT_VOLT', 'value': 0}},
    {'board_id': 'CHARGING', 'msg_type': 'SENSOR_ANALOG', 'data': {
        'time': 0, 'sensor_id': 'SENSOR_GROUND_VOLT', 'value': 0}},
    {'board_id': 'ACTUATOR_INJ', 'msg_type': 'SENSOR_ANALOG', 'data': {
        'time': 0, 'sensor_id': 'SENSOR_BATT_VOLT', 'value': 0}},
    {'board_id': 'ACTUATOR_INJ', 'msg_type': 'GENERAL_BOARD_STATUS',
        'data': {'time': 0, 'status': 'E_NOMINAL'}},
    {'board_id': 'ACTUATOR_INJ', 'msg_type': 'ACTUATOR_STATUS', 'data': {'time': 0,
                                                                         'actuator': 'ACTUATOR_INJECTOR_VALVE', 'req_state': 'ACTUATOR_UNK', 'cur_state': 'ACTUATOR_OFF'}},
    {'board_id': 'CHARGING', 'msg_type': 'GENERAL_BOARD_STATUS',
        'data': {'time': 0, 'status': 'E_NOMINAL'}},
]

t = 0
while True:
    for msg in fake_msgs:
        msg["data"]["time"] = t
        if "value" in msg["data"]:
            msg["data"]["value"] = random.randint(0, 10)
        sender.send(CHANNEL, msg)
    time.sleep(0.25)
    t += 0.25
    if t > 10:
        t = 0
