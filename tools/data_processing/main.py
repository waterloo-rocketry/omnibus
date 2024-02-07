# A coordinator for the can and daq processors, automatically taking in arguments and running opperations on parsed logs
# For a single export, it's run a few times for differnt opperations, like preview (with optional ranges) and choosing times, and for exporting the differnt streams with the option to merge
import sys
import argparse
import matplotlib.pyplot as plt
import csv
import os
import datetime
import hashlib

from tools.data_processing.can_processing import get_can_lines, get_can_cols
from tools.data_processing.daq_processing import get_daq_lines, get_daq_cols

def offset_timestamps(data1, data2):
    """Offset the timestamps of the two data sources so that they start at 0, and return the time offset that was applied to both data sources."""
    # we need logic to handle the case where one of the data sources is empty, becuase a recording might only have CAN data
    if len(data1) > 0 and len(data2) > 0:
        time_offset = min(data1[0][0], data2[0][0])
    elif len(data1) > 0:
        time_offset = data1[0][0]
    elif len(data2) > 0:
        time_offset = data2[0][0]
    else:
        raise ValueError("Both data sources are empty, can't offset timestamps.")

    for i in range(len(data1)):
        data1[i][0] -= time_offset
    for i in range(len(data2)):
        data2[i][0] -= time_offset

    return time_offset

def filter_timestamps(data, start, stop):
    """Filter the data to only include the timestamps between start and stop"""
    return [d for d in data if d[0] >= start and d[0] <= stop]

def ingest_data(file_path, mode = "a", daq_compression=True, daq_aggregate_function="average"):
    """Takes in a file path and asks the users prompts before returning the data for the columns they selected"""
    print("Parsing file...")
    
    daq_cols = []
    can_cols = []
    cols = []
    
    # get the columns from the file
    # we want to do this regardless of the mode for consistent timestamp filtering
    with open(file_path, "rb") as infile:
        daq_cols = get_daq_cols(infile)
        can_cols = get_can_cols(infile)

    if mode == "a" or mode == "d":
        cols += daq_cols
    if mode == "a" or mode == "c":
        cols += can_cols

    print("The following columns are available:")
    for i in range(len(cols)):
        prefix = "DAQ" if i < len(daq_cols) else "CAN"
        print(f"({prefix}) {i+1}: {cols[i]}")
    selection = input("Enter the numbers for the columns you want to extract, seperated by commas, or leave empty for all: ")
    
    # parse the selection into a list of indexes in the cols list
    if selection == "":
        indexes = [i for i in range(len(cols))]
    else:
        indexes = [int(i) - 1 for i in selection.replace(" ","").split(",")]

    # split the indexes into daq and can indexes, and then get the names of the selected columns
    daq_cols = [daq_cols[i] for i in indexes if i < len(daq_cols)]
    can_cols = [can_cols[i - len(daq_cols)] for i in indexes if i >= len(daq_cols)]

    print("Plotting the following columns:")
    for col in daq_cols:
        print(f"DAQ: {col}")
    for col in can_cols:
        print(f"CAN: {col}")

    print("Here's a copyable list of the numbers of the columns you selected:")
    print(",".join([str(i+1) for i in indexes]))

    # get the data for the selected columns
    with open(file_path, "rb") as infile:
        if mode == "a" or mode == "d":
            daq_data = get_daq_lines(infile, daq_cols)
            # map all None values to 0
            for i in range(len(daq_data)):
                for j in range(len(daq_data[i])):
                    if daq_data[i][j] is None:
                        daq_data[i][j] = 0
        else:
            daq_data = []
        if mode == "a" or mode == "c":
            can_data = get_can_lines(infile, can_cols)
            for i in range(len(can_data)):
                for j in range(len(can_data[i])):
                    if can_data[i][j] is None:
                        can_data[i][j] = 0
        else:
            can_data = []
    
    # offset the timestamps of the data sources so that they start at 0
    offset_timestamps(daq_data, can_data)

    # sanity check that timestamps are increasing for can
    for i in range(len(can_data) - 1):
        if int(can_data[i][0]) > int(can_data[i+1][0]): # compare the timestamps columns (redundant int cast to silence linter)
            print(f"Warning: CAN timestamp {can_data[i][0]} is greater than {can_data[i+1][0]}")

    return daq_cols, can_cols, daq_data, can_data

def data_preview(file_path, mode = "a"):
    print(f"Previewing {file_path} in mode {mode}")
    # Modes: a for all, d for daq, c for can
    if mode != "a" and mode != "d" and mode != "c":
        raise ValueError(f"Invalid mode {mode} passed to data_preview")

    daq_cols, can_cols, daq_data, can_data = ingest_data(file_path, mode)
            
    print("Pan the plot to find the time range you want to export")

    # plot the data for the selected columns
    plt.figure()

    if mode == "a":
        plt.title("DAQ and CAN data")
    elif mode == "d":
        plt.title("DAQ data")
    else:
        plt.title("CAN data")

    if mode == "a" or mode == "d":
        for i in range(len(daq_cols)):
            # plot the time column against the column for each selected colum
            plt.plot([d[0] for d in daq_data], [d[i+1] for d in daq_data], label=daq_cols[i])

    if mode == "a" or mode == "c":
        for i in range(len(can_cols)):
            plt.plot([d[0] for d in can_data], [d[i+1] for d in can_data], label=can_cols[i])

    plt.xlabel("Time (s)")
    plt.legend()
    plt.show()    

def data_export(file_path, mode = "a",daq_compression=True, daq_aggregate_function="average"):
    print(f"Exporting {file_path} in mode {mode}")
    # Modes: a for all, d for daq, c for can
    if mode != "a" and mode != "d" and mode != "c":
        raise ValueError(f"Invalid mode {mode} passed to data_export")

    daq_cols, can_cols, daq_data, can_data = ingest_data(file_path, mode, daq_compression, daq_aggregate_function)

    print("Select the time range to export, or leave empty for the start or end of the data respectively")
    start = input("Start time (s): ")
    if start == "":
        start = 0
        print("Defaulting to start of data")
    else:
        start = float(start)

    stop = input("Stop time (s): ")
    if stop == "":
        stop = float("inf")
        print("Defaulting to end of data")
    else:
        stop = float(stop)

    daq_data = filter_timestamps(daq_data, start, stop)
    can_data = filter_timestamps(can_data, start, stop)

    # print warnings if the data is empty
    if len(daq_data) == 0 and len(can_data) == 0:
        print("Warning: No data to export for the selected time range")

    # Create an export hash to identify the export
    export_hash = hashlib.md5(f"{file_path}{mode}{start}{stop}{daq_compression}{daq_aggregate_function}{daq_cols}{can_cols}{daq_data}{can_data}".encode()).hexdigest()
    export_hash = export_hash[:6]

    # write the data to a csv file for each data source
    daq_export_path = f"{file_path.replace('.log','')}_export_{export_hash}_daq.csv"
    can_export_path = f"{file_path.replace('.log','')}_export_{export_hash}_can.csv"
    if mode == "a" or mode == "d":
        with open(daq_export_path, "w") as outfile:
            writer = csv.writer(outfile)
            writer.writerow(["time"] + daq_cols)
            for line in daq_data:
                writer.writerow(line)
        
        # measure the size of the file exported
        daq_size = os.path.getsize(daq_export_path)
        formatted_daq_size = "{:.2f} MB".format(daq_size / (1024 * 1024))
        print(f"DAQ data exported to {daq_export_path} with size {formatted_daq_size}")

    if mode == "a" or mode == "c":
        with open(can_export_path, "w") as outfile:
            writer = csv.writer(outfile)
            writer.writerow(["time"] + can_cols)
            for line in can_data:
                writer.writerow(line)
        can_size = os.path.getsize(can_export_path)
        formatted_can_size = "{:.2f} MB".format(can_size / (1024 * 1024))
        print(f"CAN data exported to {can_export_path} with size {formatted_can_size}")

    # save an export manifest for information on what was exported with which settings
    manifest_text = f"Data exported from {file_path} with mode {mode} and time range {start} to {stop}, exported at {datetime.datetime.now()} with the export hash {export_hash}.\nExported columns: \nDAQ: {daq_cols} \nCAN: {can_cols} \nExported files: \nDAQ: {daq_export_path} ({formatted_daq_size}) \nCAN: {can_export_path} ({formatted_can_size}) \nDAQ export settings: \nCompression: {daq_compression} \nAggregation function: {daq_aggregate_function} \nCAN entries were filterd for stricly increasing timestamps, so may not be complete."
    with open(f"{file_path.replace('.log','')}_export_{export_hash}_manifest.txt", "w") as manifest_file:
        manifest_file.write(manifest_text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run data processing on a log file")
    parser.add_argument("file", help="The file to run on")

    parser.add_argument("-p", "--preview", help="Preview the data", action="store_true")
    parser.add_argument("-e", "--export", help="Export the data", action="store_true")

    parser.add_argument("-a", "--all", help="Plot all data", action="store_true")
    parser.add_argument("-d", "--daq", help="Plot only daq data", action="store_true")
    parser.add_argument("-c", "--can", help="Plot only can data", action="store_true")

    if len(sys.argv) == 1:
        print("Make sure to pass a log file to run on, and other options")
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    in_file_path = args.file
    processing_mode = "p"
    if args.preview:
        processing_mode = "p"
    elif args.export:
        processing_mode = "e"
    else:
        print("Defaulting to preview mode")
    
    data_mode = "a"
    if args.all:
        data_mode = "a"
    elif args.daq:
        data_mode = "d"
    elif args.can:
        data_mode = "c"
    else:
        print("Defaulting to all data sources")

    if processing_mode == "p":
        data_preview(in_file_path, data_mode)
    elif processing_mode == "e":
        data_export(in_file_path, data_mode)
    else:
        raise NotImplementedError
    