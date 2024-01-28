# Take in a log file path and yield lines of can data
from typing import List, Union

def get_can_cols(infile: str) -> List[str]:
    raise NotImplementedError

def get_can_lines(infile: str, cols=[]) -> List[List[Union[int, str]]]:
    raise NotImplementedError


if __name__ == "__main__":
    print("This file is not meant to be run directly. Run main.py instead.")
