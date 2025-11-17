# Data Processing v2 (beta) - Waterloo Rocketry

import argparse
import os
import secrets
from datetime import datetime

from sources.parsley.main import FileCommunicator


def generate_filename(log_name: str) -> str:
    # Creating file name with date + random hash
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    rand_hash = secrets.token_hex(3)
    return f"omnibus-processed-{log_name}-{timestamp}-{rand_hash}.csv"

def run_daq_command(input_file: str, output_file: str | None, channel: str) -> None:
    from processors.daq_processing import DAQDataProcessor
    out_file = output_file or generate_filename("daq")
    out_path = os.path.join(os.getcwd(), out_file)

    with open(input_file, "rb") as file:
        processor = DAQDataProcessor(file, channel)
        size = processor.process(out_path)
        print(f"SUCESS: Processed {size} bytes of DAQ data to {out_path}")

def run_logger_command(input_file: str, output_file: str | None) -> None:
    from processors.logger_processing import LoggerDataProcessor
    out_file = output_file or generate_filename("logger")
    out_path = os.path.join(os.getcwd(), out_file)

    with FileCommunicator(input_file) as file:
        processor = LoggerDataProcessor(file)
        size = processor.process(out_path)
        print(f"SUCCESS: Processed {size} bytes of logger data to {out_path}")

def main() -> None:
    # initializing command line argument parser
    parser = argparse.ArgumentParser(description="Rocketry Log Processing CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    # Adding command for daq, and file realted flags
    daq_parser = subparsers.add_parser("daq", help="Process DAQ globallog msgpack")
    daq_parser.add_argument("input_file", help="Path to the .msgpack log file")
    daq_parser.add_argument("-o", "--output", help="Optional output file name")
    daq_parser.add_argument("--fake", action="store_true", help="Use fake DAQ data")

    # Adding command for logger, and file related flags
    logger_parser = subparsers.add_parser("logger", help="Process Logger Board msgpack")
    logger_parser.add_argument("input_file", help="Path to the .msgpack log file")
    logger_parser.add_argument("-o", "--output", help="Optional output file name")

    args = parser.parse_args()
    if not os.path.isfile(args.input_file):
        parser.error(f"Input file '{args.input_file}' does not exist")

    channel = "DAQ"
    if args.command == "daq":
        if args.fake:
            channel = "DAQ/Fake"
        run_daq_command(args.input_file, args.output, channel)
    elif args.command == "logger":
        run_logger_command(args.input_file, args.output)
    else:
        raise NotImplementedError(f"Command {args.command} not implemented")

if __name__ == "__main__":
    main()
