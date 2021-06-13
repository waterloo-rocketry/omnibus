from omnibus import Receiver


def print_console(channels_filterlst):
    receiver = Receiver(CHANNEL)
    print(channels_filterlst)
    while True:
        msg = receiver.recv_message()
        if msg.channel in channels_filterlst:
            print(msg.payload)


if __name__ == '__main__':
    CHANNEL = ""  # all channels
    channel_filter = list()
    num_types = int(input("Enter number of message types: "))
    print("Enter the message types separated with new lines. ")
    for i in range(num_types):
        new = input("Enter: ")
        channel_filter.append(new)
    print_console(channel_filter)
