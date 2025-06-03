# Data Processing v2 (beta) - Waterloo Rocketry

from processors import DAQDataProcessor
import os
import argparse
from datetime import datetime
import secrets

def generate_filename() -> str:
    # Creating file name with date + random hash
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    rand_hash = secrets.token_hex(3)
    return f"omnibus-processed-daq-{timestamp}-{rand_hash}.csv"

def run_daq_command(input_file: str, output_file: str | None, channel: str) -> None:
    out_file = output_file or generate_filename()
    out_path = os.path.join(os.getcwd(), out_file)

    with open(input_file, "rb") as file:
        processor = DAQDataProcessor(file, channel)
        size = processor.process(out_path)


# TODO: Make this an actual app and not a script (and maybe GUI?)
def main() -> None:
    # initializing command line argument parser
    parser = argparse.ArgumentParser(description="Rocketry Log Processing CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    # Adding command for daq, and file realted flags
    daq_parser = subparsers.add_parser("daq", help="Process DAQ globallog msgpack")
    daq_parser.add_argument("input_file", help="Path to the .msgpack log file")
    daq_parser.add_argument("-o", "--output", help="Optional output file name")
    daq_parser.add_argument("--fake", action="store_true", help="Use fake DAQ data")

    args = parser.parse_args()
    if not os.path.isfile(args.input_file):
        parser.error(f"Input file '{args.input_file}' does not exist")

    channel = "DAQ"
    if args.command == "daq":
        if args.fake:
            channel = "DAQ/Fake"
        run_daq_command(args.input_file, args.output, channel)
    else:
        raise NotImplementedError(f"Command {args.command} not implemented")
    


if __name__ == "__main__":
    main()
