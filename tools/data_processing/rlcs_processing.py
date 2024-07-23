# Take in a log file path and yeild lines of RLCS data
from typing import List, Union, IO
import msgpack
import pandas as pd
from msgpack_sorter_unpacker import msgpackFilterUnpacker
from tools.data_processing.msgpack_sorter_unpacker import msgpackFilterUnpacker

def get_rlcs_cols(infile: IO) -> List[str]:
    """Get the columns that are present in the RLCS data in the file and returns them in the order they're encountered"""

    cols_set = set()
    cols = []
    for full_data in msgpack.Unpacker(infile):
        channel, timestamp, payload = full_data
        if channel.startswith("RLCS"):
            data = payload
            for key in data:
                if key not in cols_set:
                    cols_set.add(key)
                    cols.append(key)

    infile.seek(0)
    return cols


def get_rlcs_lines(infile: IO, cols=[],placeholder=None) -> pd.DataFrame:
    """Get all the data from the RLCS messages in the file, and return it as a pandas dataframe."""
    cols_set = set(cols)
    current_info = {col: placeholder for col in cols}
    output_lines = []
    for full_data in msgpack.Unpacker(infile):
        channel, timestamp, payload = full_data
        if channel.startswith("RLCS"):
            data = payload
            for key in data:
                if key in cols_set:
                    current_info[key] = data[key]

            output_lines.append({"timestamp": timestamp, **current_info})
            
    # load all the output lines into the dataframe
    output_df = pd.DataFrame(columns=["timestamp"] + cols, data=output_lines)

    infile.seek(0)
    return output_df


if __name__ == "__main__":
    print("This file is not meant to be run directly. Run main.py instead.")

    # testing code
    # uncomment the following to test this file

    import argparse
    parser = argparse.ArgumentParser(description="Run tests for rlcs_processing.py on a real file")
    parser.add_argument("file", help="The file to test on")

    args = parser.parse_args()
    file_path = args.file
    with open(file_path, "rb") as infile:
        print(get_rlcs_cols(infile))
        print(get_rlcs_lines(infile, get_rlcs_cols(infile)))
