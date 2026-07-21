import argparse
import serial

from omnibus import Sender

def reader(port: str):
    if port == "-":
        return input
    s = serial.Serial(port, 115200)  # listen on the RLCS port

    def _reader():
        while True:
            c = s.read()
            if c != b'F':
                continue

            output = b'F' + s.read(6 + 1) # Data + 'R'

            if output[-1] != ord('S'):
                print(f"Incorrectly terminated FYDP27SENSOR message: {[c for c in output]}")
                continue

            return output

    return _reader

def parse_fydp27sensor(line: str | bytes) -> dict[str, str] | None:
    res = {}

    res['rpm'] = (line[2] << 8 | line[1]) * 10
    res['battery_voltage'] = (line[4] << 8 | line[3]) / 10
    res['current'] = (line[6] << 8 | line[5]) / 10
        
    return res

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('port', help='the serial port to read from, or - for stdin')
    parser.add_argument('--solo', action='store_true',
                        help="Don't connect to omnibus - just print to stdout.")
    args = parser.parse_args()

    readline = reader(args.port)

    if not args.solo:
        sender = Sender()
        CHANNEL = "FYDP27SENSOR"

    while True:
        line = readline()

        if not len(line):
            continue

        parsed_data = parse_fydp27sensor(line)

        if not parsed_data:
            continue

        if not args.solo:  # if connect to omnibus
            sender.send(CHANNEL, parsed_data)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
