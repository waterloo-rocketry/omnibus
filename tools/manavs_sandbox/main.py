import msgpack
import csv
import matplotlib.pyplot as plt
import pandas as pd

from Packet import *


def retrieve_data(infile, boards, start=-1, end=float('inf')):
    # Takes logfile and a list of boards' data to read
    # Returns dictionary, 'data', with information for all boards using timestamp as keys
    # Will only return data within specific timestamp if specified

    data = dict()
    previous_timestamp = 0
    data[previous_timestamp] = {}

    # Creates first item in data, at time=0 and values=None for each board
    for board in boards:
        data[previous_timestamp][board] = None

    # Loop through log file to retrieve data, adds it to 'data'
    # Turns each logged packet into a Packet object for simplicity.
    infile.seek(0)
    for raw_packet in msgpack.Unpacker(infile):
        for packet in Packet.sort(raw_packet):

            # Check if packet is within specified timerange
            if packet.timestamp <= start or packet.timestamp >= end:
                continue

            # Check if packet is of a specified board
            elif packet.name in boards:
                # initialize the key
                if packet.timestamp not in data:
                    data[packet.timestamp] = {}

                data[packet.timestamp][packet.name] = packet.value

                # To prevent 'holes' in the dictionary, all other values are
                # copied over from the previous timestamp
                for board in boards:
                    if board not in data[packet.timestamp]:
                        data[packet.timestamp][board] = data[previous_timestamp][board]

                previous_timestamp = packet.timestamp

    # Remove the initial entry
    del data[0]

    data_list = list()
    for timestamp, items in data.items():
        data[timestamp]['Timestamp'] = timestamp
        data_list.append(items)
    del data

    return data_list


def to_csv(outfile, field_names, data):
    # Turns dict from retrieve_data() into a csv compatible list
    field_names.insert(0, 'Timestamp')

    with open(outfile, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=field_names, lineterminator='\n')
        writer.writeheader()
        writer.writerows(data)


def plot_data(infile):
    df = pd.read_csv(infile)

    ax = plt.gca()  # plot on same graph

    for col in df.columns.values[1:]:
        df.plot(x='Timestamp', y=col, kind='line', ax=ax)

    plt.show()


def main(infile):
    # Read msgpack file
    infile = open(infile, 'rb')

    # Search log file to see which sensors and actuators have readings logged.
    # Turns each logged packet into a Packet object for simplicity.
    # Adds all found boards into 'available' set
    available = set()
    for raw_packet in msgpack.Unpacker(infile):
        for packet in Packet.sort(raw_packet):
            available.add(packet.name)

    # Displays all boards found in log file from above by printing each key from
    # the 'available' set.
    # In the process, it converts the 'available' set into an ordered list
    available = list(available)
    counter = 0
    print('The following series have been detected:')
    for board in available:
        print(f'{counter}. {board}')
        counter += 1

    # User selects what boards' data they would like to read, those boards' info
    # from 'available' is added to 'selected'.
    # 'user_in' (user input as a list) is deleted to save space
    user_in = input('Enter comma-seperate what values').split(', ')
    selected = list()
    for item in user_in:
        selected.append(available[int(item)])
    del user_in

    # Retrieves the requested data and dumps it into csv
    data = retrieve_data(infile, selected)
    to_csv('testout.csv', selected, data)
    del data

    # Plot csv file
    plot_data('testout.csv')

    # retrieve data from all available boards (stored in 'responses' variable), within
    # specified timestamp, and dumps them into a csv
    time_interval = input('Select time interval (comma-separated): ').split(', ')
    data = retrieve_data(infile, available, start=int(time_interval[0]), end=int(time_interval[1]))
    to_csv('myCSV.csv', available, data)
    # ^^ THIS DOES NOT WORK UNLESS YOU PUT THE TIME IN EPOCH FORMAT (SO IT'S JUST FOR SHOW RN)


file = 'fakeniparsley.log'

if __name__ == '__main__':
    main(file)
