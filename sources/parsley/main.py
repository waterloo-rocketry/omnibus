import sys
import argparse
import message_types as mt
import serial
from serial import Serial
from omnibus import Sender

disp = serial.Serial('COM5', 9600)
sender = Sender("CAN/Parsley")


def parse_gen_cmd(msg_data):
    timestamp = msg_data[0] << 16 | msg_data[1] << 8 | msg_data[2]
    cmd = mt.gen_cmd_str[msg_data[3]]

    parsed_str = ['t=', str(timestamp) + 'ms', cmd]
    return parsed_str


def parse_valve_cmd(msg_data):
    timestamp = msg_data[0] << 16 | msg_data[1] << 8 | msg_data[2]
    valve_state = mt.valve_states_str[msg_data[3]]

    parsed_str = ['t=', str(timestamp) + 'ms', valve_state]
    return parsed_str


def parse_valve_status(msg_data):
    timestamp = msg_data[0] << 16 | msg_data[1] << 8 | msg_data[2]
    valve_state = mt.valve_states_str[msg_data[3]]
    req_valve_state = mt.valve_states_str[msg_data[4]]

    parsed_str = ['t=', str(timestamp) + 'ms', 'REQ: ' + req_valve_state,
                  'ACTUAL: ' + valve_state]
    return parsed_str


def parse_arm_cmd(msg_data):
    timestamp = msg_data[0] << 16 | msg_data[1] << 8 | msg_data[2]
    arm_state = mt.arm_states_str[msg_data[3] >> 4]
    alt_number = msg_data[3] & 0x0F

    parsed_str = ['t=', str(timestamp) + 'ms', 'ALTIMETER: ' + str(alt_number),
                  'COMAND: ' + arm_state]
    return parsed_str


def parse_arm_status(msg_data):
    timestamp = msg_data[0] << 16 | msg_data[1] << 8 | msg_data[2]
    arm_state = mt.arm_states_str[msg_data[3] >> 4]
    alt_number = msg_data[3] & 0x0F
    v_drogue = msg_data[4] << 8 | msg_data[5]
    v_main = msg_data[6] << 8 | msg_data[7]

    parsed_str = ['t=', str(timestamp) + 'ms', 'ALTIMETER: ' + str(alt_number),
                  'STATUS: ' + arm_state, 'V DROGUE: ' + str(v_drogue) + 'mV',
                  'V MAIN: ' + str(v_main) + 'mV']
    return parsed_str


def parse_debug_msg(msg_data):
    timestamp = msg_data[0] << 16 | msg_data[1] << 8 | msg_data[2]
    debug_level = (msg_data[3] & 0xf0) >> 4
    line_number = (msg_data[3] & 0x0f) << 4 | (msg_data[4] & 0xf)

    parsed_str = ['t=', str(timestamp) + 'ms', 'LVL: ' + debug_level, 'LINE: ' + line_number]
    return parsed_str


def parse_debug_printf(msg_data):
    ascii_str = [''.join(chr(e) for e in msg_data)]
    return ascii_str


def parse_board_status(msg_data):
    timestamp = msg_data[0] << 16 | msg_data[1] << 8 | msg_data[2]
    board_stat = mt.board_stat_str[msg_data[3]]

    parsed_str = ['t=', str(timestamp) + 'ms', board_stat]

    if board_stat == 'E_BUS_OVER_CURRENT':
        current = msg_data[4] << 8 | msg_data[5]
        parsed_str.append(str(current) + ' mA')

    elif board_stat == 'E_BUS_UNDER_VOLTAGE' \
            or board_stat == 'E_BUS_OVER_VOLTAGE' \
            or board_stat == 'E_BATT_UNDER_VOLTAGE' \
            or board_stat == 'E_BATT_OVER_VOLTAGE':
        voltage = msg_data[4] << 8 | msg_data[5]
        parsed_str.append(str(voltage) + ' mV')

    elif board_stat == 'E_BOARD_FEARED_DEAD' \
            or board_stat == 'E_MISSING_CRITICAL_BOARD':
        parsed_str.append(mt.board_id_str[msg_data[4]])

    elif board_stat == 'E_NO_CAN_TRAFFIC' \
            or board_stat == 'E_RADIO_SIGNAL_LOST':
        parsed_str.append(str((msg_data[4] << 8 | msg_data[5])) + 'ms')

    elif board_stat == 'E_SENSOR':
        parsed_str.append(mt.sensor_id_str[msg_data[4]])

    elif board_stat == 'E_VALVE_STATE':
        parsed_str.append('<not parsed>')

    return parsed_str


def parse_sensor_analog(msg_data):
    timestamp = msg_data[0] << 8 | msg_data[1]
    sensor_id = mt.sensor_id_str[msg_data[2]]
    value = msg_data[3] << 8 | msg_data[4]

    parsed_str = ['t=', str(timestamp) + 'ms', sensor_id, str(value)]

    return parsed_str


def parse_sensor_altitude(msg_data):
    timestamp = msg_data[0] << 16 | msg_data[1] << 8 | msg_data[2]
    altitude = int(msg_data[3] << 24 | msg_data[4] << 16 | msg_data[5] << 8 | msg_data[6])

    if altitude & 0x80000000:  # check if the value is negative
        altitude -= 0x0100000000  # if it is negative subtract what we need to undo 2's complement

    parsed_str = ['t=', str(timestamp) + 'ms', 'ALTITUDE: ' + str(altitude) + 'ft']

    return parsed_str


def parse_gps_timestamp(msg_data):
    timestamp = msg_data[0] << 16 | msg_data[1] << 8 | msg_data[2]
    utc_hours = msg_data[3]
    utc_mins = msg_data[4]
    utc_secs = msg_data[5]
    utc_dsecs = msg_data[6]
    parsed_str = ['t=', str(timestamp) + 'ms',
                  str(utc_hours) + 'hrs',
                  str(utc_mins) + 'mins',
                  str(utc_secs) + '.' + str(utc_dsecs) + 's']
    return parsed_str


def parse_gps_latitude(msg_data):
    timestamp = msg_data[0] << 16 | msg_data[1] << 8 | msg_data[2]
    degrees = msg_data[3]
    minutes = msg_data[4]
    dminutes = msg_data[5] << 8 | msg_data[6]
    direction = chr(msg_data[7])

    parsed_str = ['t=', str(timestamp) + 'ms', str(degrees) + 'deg', str(minutes) + '.'
                  + str(dminutes) + 'mins', direction]
    return parsed_str


def parse_gps_longitude(msg_data):
    timestamp = msg_data[0] << 16 | msg_data[1] << 8 | msg_data[2]
    degrees = msg_data[3]
    minutes = msg_data[4]
    dminutes = msg_data[5] << 8 | msg_data[6]
    direction = chr(msg_data[7])
    parsed_str = ['t=', str(timestamp) + 'ms', str(degrees) + 'deg', str(minutes) + '.'
                  + str(dminutes) + 'mins', direction]
    return parsed_str


def parse_gps_altitude(msg_data):
    timestamp = msg_data[0] << 16 | msg_data[1] << 8 | msg_data[2]
    altitude = msg_data[3] << 8 | msg_data[4]
    daltitude = msg_data[5]
    unit = chr(msg_data[6])
    parsed_str = ['t=', str(timestamp) + 'ms', str(altitude) + '.' + str(daltitude), unit]
    return parsed_str


def parse_gps_info(msg_data):
    timestamp = msg_data[0] << 16 | msg_data[1] << 8 | msg_data[2]
    numsat = msg_data[3]
    quality = msg_data[4]
    parsed_str = ['t=', str(timestamp) + 'ms', '#SAT=' + str(numsat), 'QUALITY=' + str(quality)]
    return parsed_str


def parse_fill_lvl(msg_data):
    timestamp = msg_data[0] << 16 | msg_data[1] << 8 | msg_data[2]
    fill_lvl = msg_data[3]
    direction = mt.fill_direction_str[msg_data[4]]
    parsed_str = ['t=', str(timestamp) + 'ms', 'LEVEL=' + str(fill_lvl),
                  'DIRECTION=' + str(direction)]
    return parsed_str


def parse_line(args, line):
    if args.format == 'logger':
        msg_counter = int(line.split()[0], 16)
        msg_sid = int((line.split(':')[0]).split()[1], 16)
        msg_data_raw = line.split(':')[1].split()

        msg_data = [int(byte, 16) for byte in msg_data_raw]
        del msg_data[-1]    # remove last element (rcv_timestamp)

        rcv_time = int(msg_data_raw[-1], 16)

    # USB format is the default
    else:
        line = line.lstrip(' \0')
        if (len(line) == 0) or (line[0] != '$'):
            return
        line = line[1:]
        msg_sid = int(line.split(':')[0], 16)
        msg_data_raw = line.split(':')[1].split(',')
        msg_data = [int(byte, 16) for byte in msg_data_raw]

    # lol @ bitwise manips in python
    msg_type = mt.msg_type_str[msg_sid & 0x7e0]
    board_id = mt.board_id_str[msg_sid & 0x1f]

    header = '[ {:<25s} {:<10s} ]'.format(msg_type, board_id)
    col_width = 15

    # Placeholder list for output formatting
    parsed_data = [header]

    # Parse each message by type
    if msg_type == 'GENERAL_CMD':
        parsed_data.extend(parse_gen_cmd(msg_data))

    elif msg_type == 'VENT_VALVE_CMD' or msg_type == 'INJ_VALVE_CMD':
        parsed_data.extend(parse_valve_cmd(msg_data))

    elif msg_type == 'ALT_ARM_CMD':
        parsed_data.extend(parse_arm_cmd(msg_data))

    elif msg_type == 'DEBUG_MSG':
        parsed_data.extend(parse_debug_msg(msg_data))

    elif msg_type == 'DEBUG_PRINTF':
        parsed_data.extend(parse_debug_printf(msg_data))

    elif msg_type == 'VENT_VALVE_STATUS' or msg_type == 'INJ_VALVE_STATUS':
        parsed_data.extend(parse_valve_status(msg_data))

    elif msg_type == 'ALT_ARM_STATUS':
        parsed_data.extend(parse_arm_status(msg_data))

    elif msg_type == 'GENERAL_BOARD_STATUS':
        parsed_data.extend(parse_board_status(msg_data))

    elif msg_type == 'SENSOR_ACC' \
            or msg_type == 'SENSOR_GYRO' \
            or msg_type == 'SENSOR_MAG':
        # not supported yet
        print(header + ' ' + line)

    elif msg_type == 'SENSOR_ALTITUDE':
        parsed_data.extend(parse_sensor_altitude(msg_data))

    elif msg_type == 'SENSOR_ANALOG':
        parsed_data.extend(parse_sensor_analog(msg_data))

    elif msg_type == 'GPS_TIMESTAMP':
        parsed_data.extend(parse_gps_timestamp(msg_data))

    elif msg_type == 'GPS_LATITUDE':
        parsed_data.extend(parse_gps_latitude(msg_data))

    elif msg_type == 'GPS_LONGITUDE':
        parsed_data.extend(parse_gps_longitude(msg_data))

    elif msg_type == 'GPS_ALTITUDE':
        parsed_data.extend(parse_gps_altitude(msg_data))

    elif msg_type == 'GPS_INFO':
        parsed_data.extend(parse_gps_info(msg_data))

    elif msg_type == 'FILL_LVL':
        parsed_data.extend(parse_fill_lvl(msg_data))

    else:
        parsed_data.extend('Message type not known, original message: ' + line)

    start_data = 0
    if msg_type == 'DEBUG_PRINTF':
        output = '{}\t'.format(parsed_data[0])
        start_data = 1
    else:
        output = '{} {} {:>10s}\t'.format(parsed_data[0], parsed_data[1], parsed_data[2])
        start_data = 3

    for data in parsed_data[start_data:]:
        output = output + '{:<20}'.format(data)

    sender.send(output)
    print(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--format', help='Options: logger, usb. Parse input in RocketCAN Logger or USB format')
    args = parser.parse_args()

    while True:

        try:

            line = disp.readline()
            line = line.strip(b'\r\n').decode('utf-8')

        except KeyboardInterrupt:
            break

        # stop when there are no lines left
        if not line:

            break

        # treat repeated messages in the same way as USB
        if line.strip() == '.':
            print('.')
            continue

         # Print the header message cause it looks cool
        if 'WATERLOO ROCKETRY CAN LOGGER' in line:
            print(line)
            continue

        try:
            parse_line(args, line)

        except KeyError:
            print('Unable to parse message: ' + line)
            continue
