import struct

import pytest

from random import random
import rlcs
from message_types import msg_index


class TestRLCS:
    def test_parse_rlcs(self):
        line = self.generate_line()
        print(line)
        parsed_data = rlcs.parse_rlcs(line)
        assert parsed_data['msg_type'] == "rlcs"

        for i, s in enumerate(msg_index):
            assert parsed_data["data"][s] == int(line[4*i+1:4*i+5], base=16)


    def test_check_rlcs_format(self):
        # first line is long, second line is short, third line is correct
        # fourth line contains an invalid character
        lines = ["W083e54e49c07998a12f6926bf1b0fc07dR",
        "W0e54e49c07998a12f6926bf1b0fc07dR",
        "W83e54e49c07998a12f6926bf1b0fc07dR",
        "W83e54e49r07998a12f6926bf1b0fc07dR"
        ]

        answers = [False, False, True, False]

        for i, line in enumerate(lines): 
            is_valid = rlcs.check_invalid_data(line)
            assert is_valid == answers[i]


    def generate_line(self):
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


if __name__=="__main__":
    t = TestRLCS
    t.test_parse_timestamp()
