import argparse
import msgpack
import csv

from argparse import Namespace
from typing import Callable, Any

messages = {}


def process_CAN_message(channel: str, payload: dict) -> None:
    """Extract the regonizable fields from the CAN message and add it to the messages dictionary"""

    field_signature = {}
    # fill in the field signature for all the matches that we have in the format {"msg_type": "ACTUATOR_STATUS", "data.actuator": "ACTUATOR_VENT_VALVE"}
    if "board_id" in payload:
        field_signature["board_id"] = payload["board_id"]
    if "msg_type" in payload:
        field_signature["msg_type"] = payload["msg_type"]
    if "data" in payload:
        if "sensor_id" in payload["data"]:
            field_signature["data.sensor_id"] = payload["data"]["sensor_id"]
        if "actuator" in payload["data"]:
            field_signature["data.actuator"] = payload["data"]["actuator"]

    sig_text = str(field_signature)
    messages[(channel, payload.get("board_id", ""), payload.get("msg_type", ""), payload.get(
        "data", {}).get("sensor_id", ""), payload.get("data", {}).get("actuator", ""), sig_text)] = payload


def process_DAQ_message(channel: str, payload: dict) -> None:
    """Get the names of the fields in the DAQ messages"""

    for field in payload["data"]:
        messages[(channel, field)] = payload["data"][(field)][0]

def process_RLCS_message(channel: str, payload: dict) -> None:
    """For each of the RLCS values, get the name of the field and the last value"""
    for name in payload:
        messages[(channel, name)] = payload[name]


def process_file(args: Namespace, process_func: Callable[[str, Any],None], headers: list[str]) -> None:
    """Process the file with the given function and headers, and write the results to a csv file. The args are used to get the log file, and the type of channel being processed."""

    with open(args.file, "rb") as infile:
        for full_data in msgpack.Unpacker(infile):
            channel, timestamp, payload = full_data
            if channel.startswith(args.channel): # check the message is in the channel we want
                process_func(channel, payload)

    raw_file_name = args.file.split('.log')[0]
    output_path = f"{raw_file_name}_unique_messages_{args.channel}.csv"
    with open(output_path, "w") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(headers)
        for key, value in messages.items():
            row = [k for k in key] + [value]
            writer.writerow(row)

        print(f"Unique messages written to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Read a messagepacked file and output all the unique messages to a text file")
    parser.add_argument("file", type=str, help="The file to read")
    parser.add_argument("channel", type=str, help="The channel to read")
    args = parser.parse_args()

    if args.channel.startswith("CAN"):
        process_file(args, process_CAN_message, [
                     "channel", "board_id", "msg_type", "sensor_id", "actuator", "signature", "sample"])
    elif args.channel.startswith("DAQ"):
        process_file(args, process_DAQ_message, ["channel", "field", "sample"])
    elif args.channel.startswith("RLCS"):
        process_file(args, process_RLCS_message, ["channel", "field", "sample"])
    else:
        print("We don't support that channel yet, use dump_whole_log.py to dump the whole log file and figure out what's in it. ")


if __name__ == "__main__":
    main()
