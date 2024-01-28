# Take in a log file path and yeild lines of daq data, with the option to be uncompressed or not
from typing import List, Union

def get_daq_cols(infile: str) -> List[str]:
    raise NotImplementedError

def get_daq_lines(infile: str, cols=[], compressed=False) -> List[List[Union[int, str]]]:
    raise NotImplementedError

if __name__ == "__main__":
    print("This file is not meant to be run directly. Run main.py instead.")