# A coordinator for the can and daq processors, automatically taking in arguments and running opperations on parsed logs
# For a single export, it's run a few times for differnt opperations, like preview (with optional ranges) and choosing times, and for exporting the differnt streams with the option to merge
import sys
import argparse

from interractions import data_preview, data_export

# ARGUMENT PARSING

def parseArguments():
    """Take parameters from the command line and parse them for the differnt modes"""
    
    parser = argparse.ArgumentParser(description="Run data processing on a log file")
    parser.add_argument("file", help="The file to run on")

    parser.add_argument("-p", "--preview", help="Preview the data", action="store_true")
    parser.add_argument("-e", "--export", help="Export the data", action="store_true")

    parser.add_argument("-a", "--all", help="Plot all data", action="store_true")
    parser.add_argument("-d", "--daq", help="Plot only daq data", action="store_true")
    parser.add_argument("-c", "--can", help="Plot only can data", action="store_true")

    parser.add_argument("-b", "--behind", help="Take the behind stream for CAN exporting", action="store_true")

    if len(sys.argv) == 1:
        print("Make sure to pass a log file to run on, and other options")
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    in_file_path = args.file
    processing_mode = "p"
    if args.preview:
        processing_mode = "p"
    elif args.export:
        processing_mode = "e"
    else:
        print("Defaulting to preview mode")

    data_mode = "a"
    if args.all:
        data_mode = "a"
    elif args.daq:
        data_mode = "d"
    elif args.can:
        data_mode = "c"
    else:
        print("Defaulting to all data sources")

    msg_packed_filtering_mode = "ahead_stream"
    if args.behind:
        msg_packed_filtering_mode = "behind_stream"

    return in_file_path, processing_mode, data_mode, msg_packed_filtering_mode


if __name__ == "__main__":
    
    in_file_path, processing_mode, data_mode, msg_packed_filtering_mode = parseArguments()

    if processing_mode == "p":
        data_preview(in_file_path, data_mode,msg_packed_filtering=msg_packed_filtering_mode)
    elif processing_mode == "e":
        data_export(in_file_path, data_mode,msg_packed_filtering=msg_packed_filtering_mode)
    else:
        raise NotImplementedError
