import struct

import pytest

from random import random
import rlcs
from message_types import msg_index


class TestRLCS:
    def test_parse_rlcs(self):
        line = self.generate_line()[1:33]
        print(line)
        parsed_data = rlcs.parse_rlcs(line)
        assert parsed_data['msg_type'] == "rlcs"

        for i, s in enumerate(msg_index):
            print(s, parsed_data["data"][s])
            assert parsed_data["data"][s] == int(line[4*i:4*i+4], base=16)


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
