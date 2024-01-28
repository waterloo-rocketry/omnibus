# Gives the option to merge both CAN and DAQ files into one, similar to mergesort merge

def merge_logs(can_file, daq_file, outfile, mode="d"):
    """Modes: d for duplicating non updated entries, e for leaving them as errors, and a for duplicating them but adding a data age column"""
    raise NotImplementedError

if __name__ == "__main__":
    print("This file is not meant to be run directly. Run main.py instead.")