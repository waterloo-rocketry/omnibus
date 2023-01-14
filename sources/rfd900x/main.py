import serial, time, re, sys, select, os
from argparse import ArgumentParser
from omnibus import Sender

CHANNEL = 'DAQ'

argparse = ArgumentParser()
argparse.add_argument('port')
argparse.add_argument('-b', '--baud', type=int, default=115200)

def main():
    args = argparse.parse_args()
    sender = Sender()
    buff = bytearray()

    with serial.Serial(args.port, args.baud, timeout=0.2) as ser:
        print("Entering AT mode")
        ser.write(b'+++')
        time.sleep(2)

        print("Enabling RSSI report")
        ser.write(b'AT&T=rssi\r\n')

        while True:
            # serial in
            c = ser.read()
            
            if c != b'\n':
                buff += c

            else:
                line = buff.decode('utf-8')
                buff = bytearray()

                match = re.findall(r'\b(\d+):(\d+)/(\d+)/\d+\b', line)
                data = {
                    "timestamp": time.time(),
                    "data": {
                        name: [value]
                        for node in match
                        for name, value in ((f"Local {node[0]}", int(node[1])), (f"Remote {node[0]}", int(node[2])))
                        if value != 0
                    }
                }

                print(line.strip())
                sender.send(CHANNEL, data)

            # serial out
            r, w, e = select.select([sys.stdin], [], [], 0)
            if r:
                line = sys.stdin.readline().strip() + '\r\n'
                ser.write(line.encode('utf-8'))

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
