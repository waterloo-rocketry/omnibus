
from typing import IO, List, Union
import msgpack
import argparse
import os

from data_saving import save_data_to_csv

def average_list(data: List[Union[int, float]]) -> Union[int, float]:
    if type(data) == int:
        return data
    return sum(data) / len(data)


def median_list(data: List[Union[int, float]]) -> Union[int, float]:
    sorted_data = sorted(data)
    length = len(sorted_data)
    if length % 2 == 0:
        return (sorted_data[length//2] + sorted_data[length//2 - 1]) / 2
    else:
        return sorted_data[length//2]


aggregation_functions = {
    "average": average_list,
    "median": median_list
}


def get_raw_daq_cols(infile: IO) -> List[str]:
    """Get the columns that are present in the DAQ data in the file and returns them in the order they're encountered"""
    cols_set = set()
    cols = []
    for full_data in msgpack.Unpacker(infile, strict_map_key=False):
        payload = full_data
        if type(payload) == int:
            continue
        data = payload['data']
        for key in data:
            if key not in cols_set:
                cols_set.add(key)
                cols.append(key)

    infile.seek(0)
    return cols

def get_raw_daq_lines(infile: IO, cols=[], compressed=True, aggregate_function_name="average") -> List[List[Union[int, str]]]:
    """Get all the data from the DAQ messages in the file, and return it as a list of lists, where each list is a line of the csv"""
    lines = []
    cols_set = set(cols)
    current_info = {col: None for col in cols}
    aggregate_function = aggregation_functions[aggregate_function_name]
    lineCount = 0
    for full_data in msgpack.Unpacker(infile, strict_map_key=False):
        payload = full_data
        if type(payload) == int:
            print(payload)
            continue
        data = payload['data']
        for key in data:
            if key in cols_set:
                if compressed:
                    current_info[key] = aggregate_function(data[key])
                else:
                    current_info[key] = data[key]

        # Depending on the compression, we either need to append just one line, or agregated entries
        if compressed:
            print([payload['timestamp']] + [current_info[col] for col in cols])
            lines.append([payload['timestamp']] + [current_info[col] for col in cols])
        else:
            raise NotImplementedError("Uncompressed DAQ data is not yet supported")
        break

    infile.seek(0)
    print(len(lines))
    print(lineCount)
    return lines

def main():
    with open("./log_2023-10-18_10-20-05.dat", "rb") as infile:
        daq_cols = get_raw_daq_cols(infile)
        daq_data = get_raw_daq_lines(infile, daq_cols)
        for column_counter in range(len(daq_data)):
            for j in range(len(daq_data[column_counter])):
                if daq_data[column_counter][j] is None:
                    daq_data[column_counter][j] = 0       
        #fileSize = save_data_to_csv("./export.csv", daq_data, daq_cols)
        #print(f"DAQ data exported to ./export.csv with size {fileSize}")


if __name__ == "__main__":
    main()
