#### NI Source Log to CSV Data Processing Script - Extrapolate Timestamps ####
# This script is used when the secondary backup logs created by the NI source itself need to be extracted.
# This script also extrapolates compressed / aggregated data points by assigning them timestamps accordingly, somewhat increasing precision.
# Last updated 2025-01-31 - Chris Yang (@ChrisYx511)

import sys
from typing import IO, List, Union
from data_saving import save_data_to_csv
import msgpack

IN_DATA = "" # Path to NI log data
OUT_CSV = "export.csv" # Output CSV file, incl. file path

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


def get_raw_daq_lines(infile: IO, cols=[]) -> List[List[Union[int, str]]]:
    last = None
    lines = []
    for msg in msgpack.Unpacker(infile, strict_map_key=False):
        if last == None:
            last = msg
            continue
        if type(msg) == int:
            print(msg)
            break        
        current_timestamp:float = msg['timestamp']
        last_timestamp:float = last['timestamp']
        data = last['data']
        length_of_agg = len(data[cols[0]])
        offset = (current_timestamp - last_timestamp) / length_of_agg

        cols_set = set(cols)

        for i in range(length_of_agg):
            current_info = {col: None for col in cols_set}
            for key in data:
                if key in cols_set:
                    current_info[key] = data[key][i]
            print([last_timestamp + i * offset] + [current_info[col] for col in cols_set])
            lines.append([last_timestamp + i * offset] + [current_info[col] for col in cols_set])
        last = msg
    return lines


def main(inpath: str, outpath: str):
    with open(inpath, "rb") as infile:
        cols = get_raw_daq_cols(infile) 
        rows = get_raw_daq_lines(infile, cols)
        filesize = save_data_to_csv(outpath, rows, cols)
        print(f"File saved to {outpath} with size {filesize}")


if __name__ == "__main__":
    if IN_DATA == "" or OUT_CSV == "":
        print("Error, unable to open or write to file. Check specified filenames in script.")
        sys.exit(1)
        
    main(IN_DATA, OUT_CSV)
