# Process log files (either from the NI source or globallog sink) into .csv

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import msgpack


def avg(data):
    return sum(data) / len(data)


# iterator to yield the data from file-link infile
def get_data(infile):
    can_last = {"ox tank": [0], "pneumatics for real": [0],
                "vent temp for real": [0], "vv": [0], "ij": [0], "ij hall": [0]}
    can_last.update({b: [0] for b in ["CHARGING", "ARMING", "ACTUATOR_INJ", "ACTUATOR_VENT", "SENSOR_INJ", "SENSOR_VENT", "GPS", "LOGGER", "TELEMETRY"]})
    start = None
    for data in msgpack.Unpacker(infile):
        # check if this was a file from the NI source (raw data) or the global log (has msgpack channels too)
        if isinstance(data, list):
            # global log format is a 3-tuple of (channel, timestamp, data)
            # ignore all non-DAQ data
            if data[0].startswith("DAQ"):
                data = data[2]
                data["data"].update(can_last)
            elif data[0].startswith("CAN/Parsley"):
                data = data[2]
                if data["msg_type"] == "SENSOR_ANALOG":
                    if data["data"]["sensor_id"] == "SENSOR_PRESSURE_OX":
                        can_last["ox tank"] = [data["data"]["value"]]
                    if data["data"]["sensor_id"] == "SENSOR_PRESSURE_PNEUMATICS":
                        can_last["pneumatics for real"] = [data["data"]["value"]]
                    if data["data"]["sensor_id"] == "SENSOR_VENT_TEMP":
                        can_last["vent temp for real"] = [data["data"]["value"]]
                elif data["msg_type"] == "ACTUATOR_STATUS":
                    data = data["data"]
                    if data["actuator"] == "ACTUATOR_VENT_VALVE":
                        can_last["vv"] = [0 if data["req_state"] == "ACTUATOR_OFF" else 100]
                    if data["actuator"] == "ACTUATOR_INJECTOR_VALVE":
                        can_last["ij"] = [0 if data["req_state"] == "ACTUATOR_OFF" else 100]
                        can_last["ij hall"] = [0 if data["cur_state"] == "ACTUATOR_OFF" else 100]
                elif data["msg_type"] == "GENERAL_BOARD_STATUS":
                    can_last[data["board_id"]] = [data["data"]["time"]]
                continue
            elif data[0].startswith("CAN"):
                data = data[2]["data"]["can_msg"]
                continue
            else:
                continue
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
    series = []
    last = 0
    for data, timestamp in get_data(infile):
        if not series:
            print("Please select from the following series:")
            keys = list(data.keys())
            for i, k in enumerate(keys):
                print(f"{i+1}: {k}")
            selection = input("Enter comma-separated indices to view: ")
            series = [keys[int(i) - 1] for i in selection.split(",")]
        # plot one data point every 0.1 seconds
        if timestamp - last < 0.1:
            continue
        last = timestamp
        times.append(timestamp)
        datapoints.append([avg(data[k]) for k in series])
    for k in range(len(series)):
        plt.plot(times, [d[k] for d in datapoints], label=series[k])
    plt.legend(loc='upper right')
    plt.show()
    start = int(input("Enter timestamp (seconds) to start export: "))
    stop = int(input("Enter timestamp (seconds) to stop export: "))
    return start, stop


# Write a subset of the full data to a CSV file
def write_csv(infile, outfile, start, stop):
    writer = csv.writer(outfile)
    channels = None  # columns of CSV file
    t = 0
    for data, timestamp in get_data(infile):
        if timestamp < start or timestamp > stop:
            continue
        if not channels:  # first time through, set the order of the channels
            channels = sorted(data.keys())
            writer.writerow(["Timestamp"] + channels)  # write header
        if timestamp < t:
            t = timestamp
            continue
        # for i in range(len(data[channels[0]])):
        #    t += 1/1000
        writer.writerow([f"{timestamp}"] +
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
