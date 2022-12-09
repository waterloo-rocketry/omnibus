import sources.parsley.message_types as mt

_func_map = {}


# decorator for parse functions to save a massive if chain
def register(msg_types):
    if isinstance(msg_types, str):
        msg_types = [msg_types]

    def wrapper(fn):
        for msg_type in msg_types:
            if msg_type in _func_map:
                raise KeyError(f"Duplicate parsers for message type {msg_type}")
            _func_map[msg_type] = fn
        return fn
    return wrapper


def _parse_timestamp(msg_data):
    return msg_data[0] << 16 | msg_data[1] << 8 | msg_data[2]


@register("GENERAL_CMD")
def parse_gen_cmd(msg_data):
    timestamp = _parse_timestamp(msg_data[:3])
    cmd = mt.gen_cmd_str[msg_data[3]]

    return {"time": timestamp, "command": cmd}


@register("ACTUATOR_CMD")
def parse_actuator_cmd(msg_data):
    timestamp = _parse_timestamp(msg_data[:3])
    actuator = mt.actuator_id_str[msg_data[3]]
    actuator_state = mt.actuator_states_str[msg_data[4]]

    return {"time": timestamp, "actuator": actuator, "req_state": actuator_state}


@register("ALT_ARM_CMD")
def parse_arm_cmd(msg_data):
    timestamp = _parse_timestamp(msg_data[:3])
    arm_state = mt.arm_states_str[msg_data[3] >> 4]
    alt_number = msg_data[3] & 0x0F

    return {"time": timestamp, "altimeter": alt_number, "state": arm_state}


@register("RESET_CMD")
def parse_reset_cmd(msg_data):
    timestamp = _parse_timestamp(msg_data[:3])
    board_id = "ALL" if msg_data[3] == 0 else mt.board_id_str[msg_data[3]]

    return {"time": timestamp, "board_id": board_id}


@register("DEBUG_MSG")
def parse_debug_msg(msg_data):
    timestamp = _parse_timestamp(msg_data[:3])
    debug_level = (msg_data[3] & 0xf0) >> 4
    line_number = (msg_data[3] & 0x0f) << 8 | msg_data[4]
    data = msg_data[5:]

    return {"time": timestamp, "level": debug_level, "line": line_number, "data": data}


@register("DEBUG_PRINTF")
def parse_debug_printf(msg_data):
    ascii_str = ''.join(chr(e) for e in msg_data if e > 0)

    return {"string": ascii_str}


@register("DEBUG_RADIO_CMD")
def parse_debug_radio_cmd(msg_data):
    ascii_str = ''.join(chr(e) for e in msg_data if e > 0)

    return {"string": ascii_str}


@register("ALT_ARM_STATUS")
def parse_arm_status(msg_data):
    timestamp = _parse_timestamp(msg_data[:3])
    arm_state = mt.arm_states_str[msg_data[3] >> 4]
    alt_number = msg_data[3] & 0x0F
    v_drogue = msg_data[4] << 8 | msg_data[5]
    v_main = msg_data[6] << 8 | msg_data[7]

    return {
        "time": timestamp, "altimeter": alt_number, "state": arm_state,
        "drogue_v": v_drogue, "main_v": v_main
    }


@register("ACTUATOR_STATUS")
def parse_actuator_status(msg_data):
    timestamp = _parse_timestamp(msg_data[:3])
    actuator = mt.actuator_id_str[msg_data[3]]
    actuator_state = mt.actuator_states_str[msg_data[4]]
    req_actuator_state = mt.actuator_states_str[msg_data[5]]

    return {"time": timestamp, "actuator": actuator, "req_state": req_actuator_state, "cur_state": actuator_state}


@register("GENERAL_BOARD_STATUS")
def parse_board_status(msg_data):
    timestamp = _parse_timestamp(msg_data[:3])
    board_stat = mt.board_stat_str[msg_data[3]]

    res = {"time": timestamp, "status": board_stat}

    if board_stat == 'E_BUS_OVER_CURRENT':
        current = msg_data[4] << 8 | msg_data[5]
        res["current"] = current

    elif board_stat in ["E_BUS_UNDER_VOLTAGE", "E_BUS_OVER_VOLTAGE",
                        "E_BATT_UNDER_VOLTAGE", "E_BATT_OVER_VOLTAGE"]:
        voltage = msg_data[4] << 8 | msg_data[5]
        res["voltage"] = voltage

    elif board_stat in ["E_BOARD_FEARED_DEAD", "E_MISSING_CRITICAL_BOARD"]:
        board_id = mt.board_id_str[msg_data[4]]
        res["board_id"] = board_id

    elif board_stat in ["E_NO_CAN_TRAFFIC", "E_RADIO_SIGNAL_LOST"]:
        time = msg_data[4] << 8 | msg_data[5]
        res["err_time"] = time

    elif board_stat == "E_SENSOR":
        sensor_id = mt.sensor_id_str[msg_data[4]]
        res["sensor_id"] = sensor_id

    elif board_stat == "E_ACTUATOR_STATE":
        expected_state = mt.actuator_states_str[msg_data[4]]
        cur_state = mt.actuator_states_str[msg_data[5]]
        res["req_state"] = expected_state
        res["cur_state"] = cur_state

    elif board_stat == "E_LOGGING":
        res["err"] = msg_data[4]

    return res


@register("SENSOR_ALTITUDE")
def parse_sensor_altitude(msg_data):
    timestamp = _parse_timestamp(msg_data[:3])
    altitude = int(msg_data[3] << 24 | msg_data[4] << 16 | msg_data[5] << 8 | msg_data[6])

    if altitude & 0x80000000:  # check if the value is negative
        altitude -= 0x0100000000  # if it is negative subtract what we need to undo 2's complement

    return {"time": timestamp, "altitude": altitude}


@register("SENSOR_TEMP")
def parse_sensor_temp(msg_data):
    timestamp = _parse_timestamp(msg_data[:3])
    sensor = msg_data[3]
    temperature = int.from_bytes(bytes(msg_data[4:7]), "big", signed=True) / 2**10

    return {"time": timestamp, "sensor_id": sensor, "temperature": temperature}


@register("SENSOR_MAG")
# the units are in micro tesla updated at 50hz
def parse_sensor_acc_gyro_mag(msg_data):
    timestamp = msg_data[0] << 8 | msg_data[1]
    x = int.from_bytes(bytes(msg_data[2:4]), "big", signed=True)
    y = int.from_bytes(bytes(msg_data[4:6]), "big", signed=True)
    z = int.from_bytes(bytes(msg_data[6:8]), "big", signed=True)

    return {"time": timestamp, "x": x, "y": y, "z": z}


# LSM303AGR, calibrated acc for +-8g
# converting analog to 16bit signed representation.
# divide by 2^16 to get to the -1 to 1 scale
# mutiply by 8 to get to the -8 to 8 scale in g
@register("SENSOR_ACC")
def parse_sensor_acc_mag(msg_data):
    timestamp = msg_data[0] << 8 | msg_data[1]
    x = int.from_bytes(bytes(msg_data[2:4]), "big", signed=True) / (2**16) * 8
    y = int.from_bytes(bytes(msg_data[4:6]), "big", signed=True) / (2**16) * 8
    z = int.from_bytes(bytes(msg_data[6:8]), "big", signed=True) / (2**16) * 8

    return {"time": timestamp, "x": x, "y": y, "z": z}

# MPU 6050 sensor which is calibrated for +-16g
# converting analog to 16bit signed representation.
# divide by 2^16 to get to the -1 to 1 scale
# mutiply by 16 to get to the -16 to 16 scale in g


@register("SENSOR_ACC2")
def parse_sensor_acc_mag(msg_data):
    timestamp = msg_data[0] << 8 | msg_data[1]
    x = int.from_bytes(bytes(msg_data[2:4]), "big", signed=True) / (2**16) * 16
    y = int.from_bytes(bytes(msg_data[4:6]), "big", signed=True) / (2**16) * 16
    z = int.from_bytes(bytes(msg_data[6:8]), "big", signed=True) / (2**16) * 16

    return {"time": timestamp, "x": x, "y": y, "z": z}

# converting analog to 16bit signed representation.
# divide by 2^16 to get to the -1 to 1 scale
# mutiply by 2000 to get to the -2000 to 2000 scale in degree/s


@register("SENSOR_GYRO")
def parse_sensor_acc_mag(msg_data):
    timestamp = msg_data[0] << 8 | msg_data[1]
    x = int.from_bytes(bytes(msg_data[2:4]), "big", signed=True) / (2**16) * 2000
    y = int.from_bytes(bytes(msg_data[4:6]), "big", signed=True) / (2**16) * 2000
    z = int.from_bytes(bytes(msg_data[6:8]), "big", signed=True) / (2**16) * 2000

    return {"time": timestamp, "x": x, "y": y, "z": z}


@register("SENSOR_ANALOG")
def parse_sensor_analog(msg_data):
    timestamp = msg_data[0] << 8 | msg_data[1]
    sensor_id = mt.sensor_id_str[msg_data[2]]
    value = msg_data[3] << 8 | msg_data[4]

    return {"time": timestamp, "sensor_id": sensor_id, "value": value}


@register("GPS_TIMESTAMP")
def parse_gps_timestamp(msg_data):
    timestamp = _parse_timestamp(msg_data[:3])
    utc_hours = msg_data[3]
    utc_mins = msg_data[4]
    utc_secs = msg_data[5]
    utc_dsecs = msg_data[6]

    return {"time": timestamp, "hrs": utc_hours, "mins": utc_mins, "secs": utc_secs, "dsecs": utc_dsecs}


@register("GPS_LATITUDE")
def parse_gps_latitude(msg_data):
    timestamp = _parse_timestamp(msg_data[:3])
    degs = msg_data[3]
    mins = msg_data[4]
    dmins = msg_data[5] << 8 | msg_data[6]
    direction = chr(msg_data[7])

    return {"time": timestamp, "degs": degs, "mins": mins, "dmins": dmins, "direction": direction}


@register("GPS_LONGITUDE")
def parse_gps_longitude(msg_data):
    timestamp = _parse_timestamp(msg_data[:3])
    degs = msg_data[3]
    mins = msg_data[4]
    dmins = msg_data[5] << 8 | msg_data[6]
    direction = chr(msg_data[7])

    return {"time": timestamp, "degs": degs, "mins": mins, "dmins": dmins, "direction": direction}


@register("GPS_ALTITUDE")
def parse_gps_altitude(msg_data):
    timestamp = _parse_timestamp(msg_data[:3])
    altitude = msg_data[3] << 8 | msg_data[4]
    daltitude = msg_data[5]
    unit = chr(msg_data[6])

    return {"time": timestamp, "altitude": altitude, "daltitude": daltitude, "unit": unit}


@register("GPS_INFO")
def parse_gps_info(msg_data):
    timestamp = _parse_timestamp(msg_data[:3])
    numsat = msg_data[3]
    quality = msg_data[4]

    return {"time": timestamp, "num_sats": numsat, "quality": quality}


@register("RADI_VALUE")
def parse_radi_value(msg_data):
    timestamp = _parse_timestamp(msg_data[:3])
    radi_board = msg_data[3]
    radi = msg_data[4] << 8 | msg_data[5]

    return {"time": timestamp, "radi_board": radi_board, "radi": radi}


@register("FILL_LVL")
def parse_fill_lvl(msg_data):
    timestamp = _parse_timestamp(msg_data[:3])
    fill_lvl = msg_data[3]
    direction = mt.fill_direction_str[msg_data[4]]

    return {"time": timestamp, "level": fill_lvl, "direction": direction}


@register("LEDS_ON")
def parse_leds_on(msg_data):
    return {}


@register("LEDS_OFF")
def parse_leds_off(msg_data):
    return {}


def parse(msg_sid, msg_data):
    # lol @ bitwise manips in python
    msg_type = mt.msg_type_str[msg_sid & 0x7e0]
    board_id = mt.board_id_str[msg_sid & 0x1f]

    res = {"msg_type": msg_type, "board_id": board_id}

    if msg_type in _func_map:
        res["data"] = _func_map[msg_type](msg_data)
    else:
        res["data"] = {"unknown": msg_data}

    return res


def parse_live_telemetry(line):
    line = line.lstrip(' \0')
    if len(line) == 0 or line[0] != '$':
        return None
    line = line[1:]

    msg_sid, msg_data = line.split(":")
    msg_data, msg_checksum = msg_data.split(";")
    msg_sid = int(msg_sid, 16)
    msg_data = [int(byte, 16) for byte in msg_data.split(",")]
    sum1 = 0
    sum2 = 0
    for c in line[:-1]:
        if c.lower() in "0123456789abcdef":
            sum1 = (sum1 + int(c, 16)) % 15
            sum2 = (sum1 + sum2) % 15
    if int(msg_checksum, 16) != sum1 ^ sum2:
        print(f"Bad checksum, expected {sum1 ^ sum2} but got {msg_checksum}")
        return None

    return msg_sid, msg_data


def parse_usb_debug(line):
    line = line.lstrip(' \0')
    if len(line) == 0 or line[0] != '$':
        return None
    line = line[1:]

    if ":" in line:
        msg_sid, msg_data = line.split(":")
        msg_sid = int(msg_sid, 16)
        msg_data = [int(byte, 16) for byte in msg_data.split(",")]
    else:
        msg_sid = int(line, 16)
        msg_data = []

    return msg_sid, msg_data


def parse_logger(line):
    # see cansw_logger/can_syslog.c for format
    msg_sid, msg_data = line[:3], line[3:]
    msg_sid = int(msg_sid, 16)
    # last 'byte' is the recv_timestamp
    msg_data = [int(msg_data[i:i+2], 16) for i in range(0, len(msg_data), 2)]
    return msg_sid, msg_data


MSG_TYPE_LEN = max([len(msg_type) for msg_type in mt.msg_type_hex])
BOARD_ID_LEN = max([len(board_id) for board_id in mt.board_id_hex])


def fmt_line(parsed_data):
    msg_type = parsed_data['msg_type']
    board_id = parsed_data['board_id']
    data = parsed_data["data"]
    res = f"[ {msg_type:<{MSG_TYPE_LEN}} {board_id:<{BOARD_ID_LEN}} ]"
    for k, v in data.items():
        res += f" {k}: {v}"
    return res
