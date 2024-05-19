import matplotlib.pyplot as plt
import csv
import os
import datetime
import hashlib

from can_processing import get_can_lines, get_can_cols
from daq_processing import get_daq_lines, get_daq_cols
from data_saving import save_data_to_csv, save_manifest
from helpers import offset_timestamps, filter_timestamps

# HELPER FUNCTION


def ingest_data(file_path: str, mode="a", daq_compression=True, daq_aggregate_function="average", msg_packed_filtering="behind_stream"):
    """Takes in a file path and asks the users prompts before returning the data for the columns they selected"""

    print("Parsing file...")

    daq_cols = []
    can_cols = []

    # get the columns from the file
    # we want to do this regardless of the mode for consistent timestamp filtering
    with open(file_path, "rb") as infile:
        daq_cols = get_daq_cols(infile)
        can_cols = get_can_cols(infile)

    column_mapping = {}

    column_counter = 1
    if mode == "a" or mode == "d":
        for col in daq_cols:
            column_mapping[("DAQ", col)] = column_counter
            column_counter += 1
    if mode == "a" or mode == "c":
        for col in can_cols:
            column_mapping[("CAN", col)] = column_counter
            column_counter += 1

    print("The following columns are available:")
    for col in column_mapping:
        print(f"{column_mapping[col]}: {col}")

    selection = input(
        "Enter the numbers or ranges with a - between (ex 3-5 for 3,4,5) for the columns you want to extract, seperated by commas, or leave empty for all: ")

    # parse the selection into a list of indexes in the cols list
    if selection == "":
        indexes = [i for i in range(1, len(column_mapping)+1)]
    else:
        selection = selection.replace(" ", "")
        indexes = []
        for part in selection.split(","):
            if "-" in part:
                start, end = part.split("-")
                indexes += [i for i in range(int(start), int(end)+1)]
            else:
                indexes.append(int(part))
    
    # remove duplicates while keeping order
    indexes = list(dict.fromkeys(indexes))

    # split the indexes into daq and can indexes, and then get the names of the selected columns
    selected_daq_cols = [col[1] for col in column_mapping if col[0]
                         == "DAQ" and column_mapping[col] in indexes]
    selected_can_cols = [col[1] for col in column_mapping if col[0]
                         == "CAN" and column_mapping[col] in indexes]

    print("Ingesting the following columns:")
    for col in selected_daq_cols:
        print(f"DAQ: {col}")
    for col in selected_can_cols:
        print(f"CAN: {col}")

    print("Here's a copyable list of the numbers of the columns you selected:")
    print(",".join([str(i) for i in indexes]))

    # get the data for the selected columns
    with open(file_path, "rb") as infile:
        if mode == "a" or mode == "d":
            daq_data = get_daq_lines(infile, selected_daq_cols,
                                     aggregate_function_name=daq_aggregate_function)
            # map all None values to 0
            for column_counter in range(len(daq_data)):
                for j in range(len(daq_data[column_counter])):
                    if daq_data[column_counter][j] is None:
                        daq_data[column_counter][j] = 0
        else:
            daq_data = []
        if mode == "a" or mode == "c":
            can_data = get_can_lines(infile, selected_can_cols,
                                     msg_packed_filtering=msg_packed_filtering)
            for column_counter in range(len(can_data)):
                for j in range(len(can_data[column_counter])):
                    if can_data[column_counter][j] is None:
                        can_data[column_counter][j] = 0
        else:
            can_data = []

    # offset the timestamps of the data sources so that they start at 0
    offset_timestamps(daq_data, can_data)

    # sanity check that timestamps are increasing for can
    for time_index in range(len(can_data) - 1):
        # compare the timestamps columns (redundant int cast to silence linter)
        if int(can_data[time_index][0]) > int(can_data[time_index+1][0]):
            print(
                f"Warning: CAN timestamp {can_data[time_index][0]} is greater than {can_data[time_index+1][0]}")

    return selected_daq_cols, selected_can_cols, daq_data, can_data

# THE MAIN DATA PROCESSING DRIVING FUNCTIONS


def data_preview(file_path: str, mode="a", msg_packed_filtering="behind_stream"):
    """A mode for previewing data with user input and plotting"""

    print(f"Previewing {file_path} in mode {mode}")
    # Modes: a for all, d for daq, c for can
    if mode != "a" and mode != "d" and mode != "c":
        raise ValueError(f"Invalid mode {mode} passed to data_preview")

    daq_cols, can_cols, daq_data, can_data = ingest_data(
        file_path, mode, msg_packed_filtering=msg_packed_filtering)

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


def data_export(file_path: str, mode="a", daq_compression=True, daq_aggregate_function="average", msg_packed_filtering="behind_stream"):
    """A mode for exporting data to csv files with user input, csv filtering, and manifest creation"""

    print(f"Exporting {file_path} in mode {mode}")
    # Modes: a for all, d for daq, c for can
    if mode != "a" and mode != "d" and mode != "c":
        raise ValueError(f"Invalid mode {mode} passed to data_export")

    # get the user to select colums and fetch the data
    daq_cols, can_cols, daq_data, can_data = ingest_data(
        file_path, mode, daq_compression, daq_aggregate_function, msg_packed_filtering=msg_packed_filtering)

    # get the time range to export
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

    # filter the data to only include the timestamps between start and stop
    daq_data = filter_timestamps(daq_data, start, stop)
    can_data = filter_timestamps(can_data, start, stop)

    # print warnings if the data is empty
    if len(daq_data) == 0 and len(can_data) == 0:
        print("Warning: No data to export for the selected time range")

    # Create an export hash to identify the export
    export_hash = hashlib.md5(
        f"{file_path}{mode}{start}{stop}{daq_compression}{daq_aggregate_function}{daq_cols}{can_cols}{daq_data}{can_data}".encode()).hexdigest()
    export_hash = export_hash[:6]

    formatted_daq_size = "N/A"
    formatted_can_size = "N/A"
    # write the data to a csv file for each data source
    daq_export_path = f"{file_path.replace('.log','')}_export_{export_hash}_daq.csv"
    can_export_path = f"{file_path.replace('.log','')}_export_{export_hash}_can.csv"
    if mode == "a" or mode == "d":
        formatted_daq_size = save_data_to_csv(daq_export_path, daq_data, daq_cols)
        print(f"DAQ data exported to {daq_export_path} with size {formatted_daq_size}")

    if mode == "a" or mode == "c":
        formatted_can_size = save_data_to_csv(can_export_path, can_data, can_cols)
        print(f"CAN data exported to {can_export_path} with size {formatted_can_size}")

    # save an export manifest for information on what was exported with which settings
    save_manifest({
        "file_path": file_path,
        "mode": mode,
        "start": start,
        "stop": stop,
        "export_hash": export_hash,
        "daq_cols": daq_cols,
        "can_cols": can_cols,
        "daq_export_path": daq_export_path,
        "can_export_path": can_export_path,
        "formatted_daq_size": formatted_daq_size,
        "formatted_can_size": formatted_can_size,
        "daq_compression": daq_compression,
        "daq_aggregate_function": daq_aggregate_function,
        "msg_packed_filtering": msg_packed_filtering
    })
