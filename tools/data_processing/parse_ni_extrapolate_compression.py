from typing import IO, List, Union
from data_saving import save_data_to_csv
import msgpack


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


def main():
    with open("./log_2023-10-18_10-20-05.dat", "rb") as infile:
        cols = get_raw_daq_cols(infile) 
        rows = get_raw_daq_lines(infile, cols)
        filesize = save_data_to_csv("./export", rows, cols)
        print(f"File saved to ./export.csv with size {filesize}")


if __name__ == "__main__":
    main()