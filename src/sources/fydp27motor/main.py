import argparse
import serial

from omnibus import Sender

def reader(port: str):
    if port == "-":
        return input
    s = serial.Serial(port, 2000000)  # listen on the RLCS port

    def _reader():
        while True:
            c = s.read()
            if c != b'F':
                continue

            output = b'F' + s.read(2 + 1) # Data + 'R'

            if output[-1] != ord('M'):
                print(f"Incorrectly terminated FYDP27MOTOR message: {[c for c in output]}")
                continue

            return output

    return _reader

def parse_fydp27motor(line: str | bytes) -> dict[str, str] | None:
    res = {}

    if isinstance(line, bytes):
        line = line.decode('utf-8', errors='ignore')
    
    if(line[1] == 'f'):
        res['throttle'] = '10'
    else:
        res['throttle'] = line[1]

    if(line[2] == '1'):
        res['onoffswitch'] = 'ON'
    elif(line[2] == '2'):
        res['onoffswitch'] = 'ABORT'
    else:
        res['onoffswitch'] = 'OFF'
        
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
        CHANNEL = "FYDP27MOTOR"

    while True:
        line = readline()

        if not len(line):
            continue

        parsed_data = parse_fydp27motor(line)

        if not parsed_data:
            continue

        if not args.solo:  # if connect to omnibus
            sender.send(CHANNEL, parsed_data)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
