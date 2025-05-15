# Data Processing v2 (beta) - Waterloo Rocketry

from processors import DAQDataProcessor
import os
import argparse
from datetime import datetime
import secrets

CHANNEL = "DAQ"

def generate_filename(input_file: str) -> str:
    # Creating file name with date + random hash
    """
    Generates a unique output filename for processed DAQ data.
    
    The filename includes a fixed prefix, the current timestamp, and a random
    6-character hexadecimal string, ending with a `.csv` extension.
    
    Args:
        input_file: Path to the original input file (not used in naming).
    
    Returns:
        A unique, timestamped filename suitable for saving processed data.
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    rand_hash = secrets.token_hex(3)
    return f"omnibus-processed-daq-{timestamp}-{rand_hash}.csv"

def run_daq_command(input_file: str, output_file: str | None):
    """
    Processes a DAQ log file and writes the results to a CSV file.
    
    If an output filename is not provided, a unique one is generated in the same directory as the input file.
    """
    out_file = output_file or generate_filename(input_file)
    out_path = os.path.join(os.path.dirname(input_file), out_file)

    with open(input_file, "rb") as file:
        processor = DAQDataProcessor(file, CHANNEL)
        size = processor.process(out_path)


# TODO: Make this an actual app and not a script (and maybe GUI?)
def main() -> None:
    # initializing command line argument parser
    """
    Parses command-line arguments and dispatches to the appropriate log processing command.
    
    Initializes a CLI with a 'daq' subcommand for processing DAQ log files, requiring an input file and optionally accepting an output filename. Executes the corresponding processing function based on user input.
    """
    parser = argparse.ArgumentParser(description="Rocketry Log Processing CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    # Adding command for daq, and file realted flags
    daq_parser = subparsers.add_parser("daq", help="Process DAQ globallog msgpack")
    daq_parser.add_argument("input_file", help="Path to the .msgpack log file")
    daq_parser.add_argument("-o", "--output", help="Optional output file name")

    args = parser.parse_args()

    if args.command == "daq":
        run_daq_command(args.input_file, args.output)
    else:
        raise NotImplementedError(f"Command {args.command} not implemented")
    


if __name__ == "__main__":
    main()
