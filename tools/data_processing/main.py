# A coordinator for the can and daq processors, automatically taking in arguments and running opperations on parsed logs
# For a single export, it's run a few times for differnt opperations, like preview (with optional ranges) and choosing times, and for exporting the differnt streams with the option to merge
import sys
import argparse
import matplotlib.pyplot as plt
import csv

from tools.data_processing.can_processing import get_can_lines, get_can_cols
from tools.data_processing.daq_processing import get_daq_lines, get_daq_cols
from tools.data_processing.log_merger import merge_logs

def offset_timestamps(data1, data2): # assumes data is sorted by timestamp
    if len(data1) > 0 and len(data2) > 0:
        time_offset = min(data1[0][0], data2[0][0])
    elif len(data1) > 0:
        time_offset = data1[0][0]
    elif len(data2) > 0:
        time_offset = data2[0][0]

    for i in range(len(data1)):
        data1[i][0] -= time_offset
    for i in range(len(data2)):
        data2[i][0] -= time_offset

    return time_offset

def data_preview(file_path, mode = "a"):
    print(f"Previewing {file_path} in mode {mode}")
    print("Parsing file...")
    # Modes: a for all, d for daq, c for can
    if mode != "a" and mode != "d" and mode != "c":
        raise ValueError(f"Invalid mode {mode} passed to data_preview")

    daq_cols = []
    can_cols = []
    cols = []
    if mode == "a" or mode == "d":
        with open(file_path, "rb") as infile:
            daq_cols = get_daq_cols(infile)
            cols += daq_cols
    if mode == "a" or mode == "c":
        with open(file_path, "rb") as infile:
            can_cols = get_can_cols(infile)
            cols += can_cols

    print("The following columns are available:")
    for i in range(len(cols)):
        print(f"{i+1}: {cols[i]}")
    selection = input("Enter the columns you want to plot, seperated by commas, or leave empty for all: ")
    
    if selection == "":
        indexes = [i for i in range(len(cols))]
    else:
        indexes = [int(i) - 1 for i in selection.split(",")]

    daq_selected_cols = [daq_cols[i] for i in indexes if i < len(daq_cols)]
    can_selected_cols = [can_cols[i - len(daq_cols)] for i in indexes if i >= len(daq_cols)]

    print("Plotting the following columns:")
    for col in daq_selected_cols:
        print(f"DAQ: {col}")
    for col in can_selected_cols:
        print(f"CAN: {col}")

    with open(file_path, "rb") as infile:
        if mode == "a" or mode == "d":
            daq_data = get_daq_lines(infile, daq_selected_cols)
            # map all None values to 0
            for i in range(len(daq_data)):
                for j in range(len(daq_data[i])):
                    if daq_data[i][j] is None:
                        daq_data[i][j] = 0
        else:
            daq_data = []
        if mode == "a" or mode == "c":
            can_data = get_can_lines(infile, can_selected_cols)
            for i in range(len(can_data)):
                for j in range(len(can_data[i])):
                    if can_data[i][j] is None:
                        can_data[i][j] = 0
        else:
            can_data = []
    
    
    offset_timestamps(daq_data, can_data)

    # check that timestamps are increasing for can
    for i in range(len(can_data) - 1):
        if can_data[i][0] > can_data[i+1][0]:
            print(f"CAN timestamp {can_data[i][0]} is greater than {can_data[i+1][0]}")
        
    # plot the data
    plt.figure()
    if mode == "a":
        plt.title("DAQ and CAN data")
    elif mode == "d":
        plt.title("DAQ data")
    else:
        plt.title("CAN data")

    if mode == "a" or mode == "d":
        for i in range(len(daq_selected_cols)):
            plt.plot([d[0] for d in daq_data], [d[i+1] for d in daq_data], label=daq_selected_cols[i])

    if mode == "a" or mode == "c":
        for i in range(len(can_selected_cols)):
            plt.plot([d[0] for d in can_data], [d[i+1] for d in can_data], label=can_selected_cols[i])

    plt.xlabel("Time (s)")
    plt.legend()
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run data processing on a log file")
    parser.add_argument("file", help="The file to run on")

    parser.add_argument("-p", "--preview", help="Preview the data", action="store_true")
    parser.add_argument("-e", "--export", help="Export the data", action="store_true")
    parser.add_argument("-m", "--merge", help="Merge the data", action="store_true")

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
    elif args.merge:
        processing_mode = "m"
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
    else:
        raise NotImplementedError
    