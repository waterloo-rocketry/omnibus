# Data Processing v2 (beta) - Waterloo Rocketry

import argparse
import os
import secrets
from datetime import datetime
from typing import cast

from sources.parsley.main import FileCommunicator

from processors.daq_processing import (
        DAQDataProcessor,
        DAQHostSyncProcessor_V3,
        DAQDataProcessor_V3,
)

DAQ_CHANNEL_BY_SOURCE = {
    "ni": "DAQ/ni",
    "ljm": "DAQ/ljm",
    "fake": "DAQ/Fake",
}


def generate_filename(log_name: str) -> str:
    # Creating file name with date + random hash
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    rand_hash = secrets.token_hex(3)
    return f"omnibus-processed-{log_name}-{timestamp}-{rand_hash}.csv"


def resolve_daq_channel(source: str | None, use_fake: bool = False) -> str | None:
    if use_fake:
        return DAQ_CHANNEL_BY_SOURCE["fake"]

    if source is None:
        return None

    normalized_source = source.strip()
    if normalized_source == "DAQ" or normalized_source.startswith("DAQ/"):
        return normalized_source

    return DAQ_CHANNEL_BY_SOURCE.get(
        normalized_source.lower(), f"DAQ/{normalized_source.lower()}"
    )


def run_daq_command(
    input_file: str,
    output_file: str | None,
    channel: str | None,
    v3: bool = True,
    host_sync: bool = False,
) -> None:
    if host_sync and not v3:
        raise ValueError("The --host-sync mode requires V3 DAQ messages and is incompatible with --v2")

    if host_sync:
        processor_class = DAQHostSyncProcessor_V3
    elif v3:
        processor_class = DAQDataProcessor_V3
    else:
        processor_class = DAQDataProcessor

    out_file = output_file or generate_filename("daq")
    out_path = os.path.join(os.getcwd(), out_file)

    with open(input_file, "rb") as file:
        processor = processor_class(file, channel)
        size = processor.process(out_path)
        print(f"SUCESS: Processed {size} bytes of DAQ data to {out_path}")

def run_logger_command(input_file: str, output_file: str | None) -> None:
    from .processors.logger_processing import LoggerDataProcessor
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
    _ = daq_parser.add_argument("input_file", help="Path to the .msgpack log file")
    _ = daq_parser.add_argument("-o", "--output", help="Optional output file name")
    _ = daq_parser.add_argument("--fake", action="store_true", help="Use fake DAQ data")
    _ = daq_parser.add_argument(
        "--source",
        help="DAQ source to process, such as ni, ljm, fake, or a full DAQ channel name",
    )
    _ = daq_parser.add_argument(
        "--v2",
        action="store_true",
        help="Use legacy V2 message format instead of the default V3 parser",
    )
    _ = daq_parser.add_argument(
        "--host-sync",
        action="store_true",
        help="Recompute DAQ timestamps from host timestamps for one or more V3 DAQ sources",
    )

    # Adding command for logger, and file related flags
    logger_parser = subparsers.add_parser("logger", help="Process Logger Board msgpack")
    _ = logger_parser.add_argument("input_file", help="Path to the .msgpack log file")
    _ = logger_parser.add_argument("-o", "--output", help="Optional output file name")

    args = parser.parse_args()
    input_file = cast(str, args.input_file)
    command = cast(str, args.command)
    output = cast(str | None, getattr(args, "output", None))

    if not os.path.isfile(input_file):
        parser.error(f"Input file '{input_file}' does not exist")

    if command == "daq":
        channel = resolve_daq_channel(
            cast(str | None, getattr(args, "source", None)),
            use_fake=cast(bool, getattr(args, "fake", False)),
        )
        use_v3 = not cast(bool, getattr(args, "v2", False))
        run_daq_command(
            input_file,
            output,
            channel,
            v3=use_v3,
            host_sync=cast(bool, getattr(args, "host_sync", False)),
        )
    elif command == "logger":
        run_logger_command(input_file, output)
    else:
        raise NotImplementedError(f"Command {command} not implemented")

if __name__ == "__main__":
    main()
