from omnibus import Receiver

def print_console():
    receiver = Receiver(SERVER, CHANNEL)
    print(txt_filter)
    while True:
        msg = receiver.recv_message()
        if msg.channel.lower() in txt_filter:
            print(f"{msg.payload}\n")

if __name__ == '__main__':
    CHANNEL = ""  # all channels
    SERVER = "tcp://localhost:5076"  # server
    txt_filter = list()
    num_types = int(input("Enter number of message types: "))
    print("Enter the message types separated with new lines. ")
    for i in range(num_types):
        new = input("Enter: ")
        txt_filter.append(new.lower())
    print_console()
