# Take in a log file path and yeild lines of daq data, with the option to be uncompressed or not
from typing import List, Union, IO
import msgpack
import pandas as pd
from msgpack_sorter_unpacker import msgpackFilterUnpacker
from tools.data_processing.msgpack_sorter_unpacker import msgpackFilterUnpacker

def average_list(data : List[Union[int, float]]) -> Union[int, float]:
    return sum(data) / len(data)

def median_list(data : List[Union[int, float]]) -> Union[int, float]:
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


def get_daq_cols(infile: IO) -> List[str]:
    """Get the columns that are present in the DAQ data in the file and returns them in the order they're encountered"""

    cols_set = set()
    cols = []
    for full_data in msgpack.Unpacker(infile):
        channel, timestamp, payload = full_data
        if channel.startswith("DAQ"):
            data = payload["data"]
            for key in data:
                if key not in cols_set:
                    cols_set.add(key)
                    cols.append(key)

    infile.seek(0)
    return cols


def get_daq_lines(infile: IO, cols=[], compressed=True, aggregate_function_name="average",placeholder=None) -> pd.DataFrame:
    """Get all the data from the DAQ messages in the file, and return it as a pandas dataframe."""
    cols_set = set(cols)
    current_info = {col: placeholder for col in cols}
    aggregate_function = aggregation_functions[aggregate_function_name]
    output_lines = []
    for full_data in msgpack.Unpacker(infile):
        channel, timestamp, payload = full_data
        if channel.startswith("DAQ"):
            data = payload["data"]
            for key in data:
                if key in cols_set:
                    if compressed:
                        current_info[key] = aggregate_function(data[key])
                    else:
                        current_info[key] = data[key]

            # Depending on the compression, we either need to append just one line, or agregated entries
            if compressed:
                output_lines.append({"timestamp": timestamp, **current_info})
            else:
                raise NotImplementedError("Uncompressed DAQ data is not yet supported")
            
    # load all the output lines into the dataframe
    output_df = pd.DataFrame(columns=["timestamp"] + cols, data=output_lines)

    infile.seek(0)
    return output_df


if __name__ == "__main__":
    print("This file is not meant to be run directly. Run main.py instead.")

    # testing code
    # uncomment the following to test this file

    # import argparse
    # parser = argparse.ArgumentParser(description="Run tests for daq_processing.py on a real file")
    # parser.add_argument("file", help="The file to test on")

    # args = parser.parse_args()
    # file_path = args.file
    # with open(file_path, "rb") as infile:
    #     print(get_daq_cols(infile))
    #     print(str(average_list))
    #     print(get_daq_lines(infile, ["Fake1", "Fake2", "Fake3", "Fake4", "Fake5"], compressed=True, aggregate_function=average_list))
