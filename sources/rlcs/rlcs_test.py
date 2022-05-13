import struct

import pytest

from random import random


def generate_line():
    """
        Dummy function to generate a random line of valid RLCS-format input data
        W[xxxx][xxxx]...[xxxx]R where xxxx = a hexadecimal number
    """

    line = "W"

    for _ in range(8):
        hexnum = hex(int(random()*65536))[2:6]
        h = hexnum.rjust(4, '0')
        line += h

    line = line + "R"
    return line
