# Take in a log file object and yield lines of can data
import msgpack
import csv
from typing import List, Union

from tools.data_processing.can_field_definitions import CAN_FIELDS
from tools.data_processing.msgpack_sorter_unpacker import msgpackSorterUnpacker

def get_can_cols(infile) -> List[str]:
    cols = [] # the colums in the order they're encountered
    cols_set = set()
    for full_data in msgpack.Unpacker(infile): # here, being unsorted is ok
        # all CAN messages are passed from the rocket through parsley into the log, so we can just check for the parsley header
        channel, timestamp, payload = full_data
        if channel.startswith("CAN/Parsley"): 
            for field in CAN_FIELDS:
                if field.match(payload) and field.csv_name not in cols_set:
                    cols_set.add(field.csv_name)
                    cols.append(field.csv_name)
                continue

    return cols

def get_can_lines(infile, cols=[]) -> List[List[Union[int, str]]]:
    cols_set = set(cols)
    current_info = {col: None for col in cols}
    output_csv_lines = []
    for full_data in msgpackSorterUnpacker(infile):
        channel, timestamp, payload = full_data
        if channel.startswith("CAN/Parsley"): 
            matched = False
            for field in CAN_FIELDS:
                # match the payload to a field, and check if we're exporting it
                if field.match(payload) and field.csv_name in cols_set:
                    current_info[field.csv_name] = field.read(payload)
                    matched = True
            
            # no need for an updated line if we didnt update any of the values we're tracking
            if not matched:
                continue

            # if we've matched, we should output the current info and write a new line
            out_line = [timestamp]
            for col in cols:
                out_line.append(current_info[col])

            output_csv_lines.append(out_line)

    return output_csv_lines


if __name__ == "__main__":
    print("This file is not meant to be run directly. Run main.py instead.")

    # for now we're just testing though
    import argparse
    parser = argparse.ArgumentParser(description="Run tests for can_processing.py on a real file")
    parser.add_argument("file", help="The file to test on")
    args = parser.parse_args()
    file_path = args.file

    print("Testing get_can_cols")
    with open(file_path, "rb") as infile:
        print(get_can_cols(infile))
        print("Done testing get_can_cols")

    print("Testing get_can_lines for 10th line")
    with open(file_path, "rb") as infile:
        print(get_can_lines(infile, ['general_status', 'ox_tank', 'injector_valve_cur_status', 'vent_temp', 'vent_valve_status', 'injector_valve_req_status', 'pneumatics_pressure'])[10])
        print("Done testing get_can_lines")

    print("Testing full_extract_can")
    with open(file_path, "rb") as infile:
        with open("test-can-out.csv", "w") as outfile:
            writer = csv.writer(outfile)
            writer.writerow(["time"] + ['ox_tank', 'injector_valve_cur_status', 'vent_temp', 'vent_valve_status', 'injector_valve_req_status', 'pneumatics_pressure'])
            for line in get_can_lines(infile, ['ox_tank', 'injector_valve_cur_status', 'vent_temp', 'vent_valve_status', 'injector_valve_req_status', 'pneumatics_pressure']):
                writer.writerow(line)
