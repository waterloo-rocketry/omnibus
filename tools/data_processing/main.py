# Process log files (either from the NI source or globallog sink) into .csv

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import msgpack

# These are the series which are initially plotted in order to determine the range of full data to export
TIME_IDENTIFICATION_SENSORS = [
    "PNew3 (PT-3) - Fuel Tank",
    "PNew4 (PT-2) - Ox Tanks",
    "PNew (PT-5) - Ox Injector",
    "PNew2 - Fuel Injector"
]


def avg(data):
    return sum(data) / len(data)


# iterator to yield the data from file-link infile
def get_data(infile):
    start = None
    for data in msgpack.Unpacker(infile):
        # check if this was a file from the NI source (raw data) or the global log (has msgpack channels too)
        if isinstance(data, list):
            # global log format is a 3-tuple of (channel, timestamp, data)
            # ignore all non-DAQ data
            if not data[0].startswith("DAQ"):
                continue
            data = data[2]
        # the data format is the same from here on out
        data, timestamp = data["data"], data["timestamp"]
        if start is None:
            start = timestamp
        timestamp -= start
        yield data, timestamp
    # so that we can read again from the same file
    infile.seek(0)


# determine the range of data to export by plotting a handful of channels
def get_range(infile):
    datapoints = []
    times = []
    last = 0
    for data, timestamp in get_data(infile):
        # plot one data point every 0.1 seconds
        if timestamp - last < 0.1:
            continue
        last = timestamp
        times.append(timestamp)
        datapoints.append([avg(data[k]) for k in TIME_IDENTIFICATION_SENSORS])
    for k in range(len(TIME_IDENTIFICATION_SENSORS)):
        plt.plot(times, [d[k] for d in datapoints])
    plt.show()
    start = int(input("Enter timestamp (seconds) to start export: "))
    stop = int(input("Enter timestamp (seconds) to stop export: "))
    return start, stop


# Write a subset of the full data to a CSV file
def write_csv(infile, outfile, start, stop):
    writer = csv.writer(outfile)
    channels = None  # columns of CSV file
    for data, timestamp in get_data(infile):
        if timestamp < start or timestamp > stop:
            continue
        if not channels:  # first time through, set the order of the channels
            channels = sorted(data.keys())
            writer.writerow(["Timestamp"] + channels)  # write header
        writer.writerow([f"{timestamp - start:.6f}"] +
                        [f"{avg(data[c]):.6f}" for c in channels])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', help='The .dat / .log file to read from')
    args = parser.parse_args()

    with open(args.file, 'rb') as infile:
        start, stop = get_range(infile)

        outfilename = Path(args.file).with_suffix(".csv")
        with open(outfilename, 'w', encoding='utf-8', newline='') as outfile:
            write_csv(infile, outfile, start, stop)

    print(f"Successfully wrote data to {outfilename}")


if __name__ == "__main__":
    main()
