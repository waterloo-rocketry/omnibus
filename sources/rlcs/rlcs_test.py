import struct

import pytest

import random
import rlcs.rlcs as rlcs
from rlcs.config import MSG_INDEX


class TestRLCS:
    def test_parse_rlcs(self):
        line = self.generate_line()
        parsed_data = rlcs.parse_rlcs(line)
        assert parsed_data

        for i, s in enumerate(MSG_INDEX):
            assert parsed_data[s] == int(line[4*i+1:4*i+5], base=16)

    def test_check_rlcs_format(self):
        # first line is long, second line is short, third line is correct
        # fourth line contains an invalid character
        lines = ["W083e54e49c07998a12f6926bf1b0fc07dR",
                 "W0e54e49c07998a12f6926bf1b0fc07dR",
                 "W83e54e49c07998a12f6926bf1b0fc07dR",
                 "W83e54e49r07998a12f6926bf1b0fc07dR",
                 "as1-0dfa`slfakd~~fjal garbage data"
                 ]

        answers = [False, False, True, False, False]

        for i, line in enumerate(lines):
            is_valid = rlcs.check_data_is_valid(line)
            assert is_valid == answers[i]

    def generate_line(self):
        """
            Dummy function to generate a random line of valid RLCS-format input data
            W[xxxx][xxxx]...[xxxx]R where xxxx = a hexadecimal number
        """
        hexnums = ''.join(random.choices("ABCDEF0123456789", k=4*len(MSG_INDEX)))
        return "W" + hexnums + "R"
