import sys

from omnibus import Receiver

def print_console():
    receiver = Receiver(CHANNEL)
    print('Cmd line arguments entered: ')
    print(sys.argv)
    while True:
        msg = receiver.recv_message()
        if msg.channel in sys.argv:
            print(msg.payload)

if __name__ == '__main__':
    CHANNEL = ""  # all channels
    print_console()
