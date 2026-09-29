import argparse
import serial
import time

from omnibus import Sender

# Data packet format:
# Unless otherwise specified, each byte shall be treated as unsigned integer(uint8_t in C)
#  0 - ASCII Character 'F'
#  1 - State: ASCII character, INIT(I), READY(R), VIBRATION_ABORT(V), MOTOR_THERM_ABORT(M), BATTERY_THERM_ABORT(B), ESC_ABORT(E, not used)
#  2 - RPM LSB - divided by 10
#  3 - RPM MSB - divided by 10
#  4 - Voltage LSB - Volts, multiplied by 10
#  5 - Voltage MSB - Volts, multiplied by 10
#  6 - Current LSB - Amps, multiplied by 10
#  7 - Current MSB - Amps, multiplied by 10
#  8 - ESC Temperature - Celsius, added 20 (range -20 - 235)
#  9 - Acceleration LSB - Unit TBD
# 10 - Acceleration MSB - Unit TBD
# 11 - LiPo 1 Temperature - Celsius, added 20 (range -20 - 235)
# 12 - LiPo 2 Temperature - Celsius, added 20 (range -20 - 235)
# 13 - FTS-401 Coolant Inlet Temperature - Celsius, added 20 (range -20 - 235)
# 14 - MTS-402 Motor Temperature - Celsius, added 20 (range -20 - 235)
# 15 - FTS-403 Coolant Outlet Temperature - Celsius, added 20 (range -20 - 235)
# 16 - ASCII Character 'M'

def reader(port: str):
    if port == "-":
        return input
    s = serial.Serial(port, 115200)  # listen on the RLCS port

    def _reader():
        while True:
            c = s.read()
            if c != b'F':
                continue

            output = b'F' + s.read(15 + 1) # Data + 'S'

            if output[-1] != ord('S'):
                print(f"Incorrectly terminated FYDP27SENSOR message: {[c for c in output]}")
                continue

            return output

    return _reader

def parse_fydp27sensor(line: str | bytes) -> dict[str, str] | None:
    res = {}

    if(line[1] == 'I'):
        res['state'] = 'INIT'
    elif(line[1] == 'R'):
        res['state'] = 'READY'
    elif(line[1] == 'V'):
        res['state'] = 'VIBRATION_ABORT'
    elif(line[1] == 'M'):
        res['state'] = 'MOTOR_THERM_ABORT'
    elif(line[1] == 'B'):
        res['state'] = 'BATTERY_THERM_ABORT_ABORT'
    elif(line[1] == 'E'):
        res['state'] = 'ESC_ABORT'
    else:
        res['state'] = 'INVALID'
    res['rpm'] = (line[3] << 8 | line[2]) * 10
    res['battery_voltage'] = (line[5] << 8 | line[4]) / 10
    res['current'] = (line[7] << 8 | line[6]) / 10
    res['esc_temp'] = line[8] - 20
    res['max_accel'] = (line[10] << 8 | line[9])
    res['lipo_temp_1'] = line[11] - 20
    res['lipo_temp_2'] = line[12] - 20
    res['fts401_coolant_inlet_temp'] = line[13] - 20
    res['mts402_motor_temp'] = line[14] - 20
    res['fts403_coolant_outlet_temp'] = line[15] - 20

    return res

def fake_parse_fydp27sensor() -> dict[str, str] | None:
    res = {}

    res['state'] = 'READY'
    res['rpm'] = 12345
    res['battery_voltage'] = 12.34
    res['current'] = 234
    res['esc_temp'] = 25
    res['max_accel'] = 67
    res['lipo_temp_1'] = 12
    res['lipo_temp_2'] = 23
    res['fts401_coolant_inlet_temp'] = 34
    res['mts402_motor_temp'] = 45
    res['fts403_coolant_outlet_temp'] = 56

    return res

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('port', help='the serial port to read from, or - for stdin')
    parser.add_argument('--solo', action='store_true',
                        help="Don't connect to omnibus - just print to stdout.")
    parser.add_argument('--fake', action="store_true",
                        help="Don't read from hardware - uses fake data. Give any value for a port")
    args = parser.parse_args()

    if not args.fake:
        readline = reader(args.port)

    if not args.solo:
        sender = Sender()
        CHANNEL = "FYDP27SENSOR"

    while True:
        if not args.fake:
            line = readline()
            if not len(line):
                continue
            parsed_data = parse_fydp27sensor(line)
        else:
            time.sleep(0.1)
            parsed_data = fake_parse_fydp27sensor()

        if not parsed_data:
            continue

        if not args.solo:  # if connect to omnibus
            sender.send(CHANNEL, parsed_data)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
