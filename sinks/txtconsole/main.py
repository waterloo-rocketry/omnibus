import sys

from omnibus import Receiver

def print_console(channels_filter):
    receiver = Receiver(CHANNEL)
    print('Filter/Cmd line arguments entered: ')
    print(channels_filter)
    while True:
        msg = receiver.recv_message()
        if msg.channel in channels_filter:
            print(msg.payload)

if __name__ == '__main__':
    CHANNEL = ""  # all channels
    print_console(sys.argv[1:])
