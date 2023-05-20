import struct

from config import MESSAGE_FORMAT

STRUCT_FMT = "<" + ''.join(k[1] for k in MESSAGE_FORMAT)

def print_data(parsed):
    for k, v in parsed.items():
        print(f"{k}:\t{v}")

def parse_rlcs(line):
    '''parses data as well as checks for data validity 
        returns none if data is invalid 
    '''
    if not check_data_is_valid(line):
        return None

    line = line[1:len(line)-1]
    fields = struct.unpack(STRUCT_FMT, line)
    res = {}
    # items
    for (name, _), value in zip(MESSAGE_FORMAT, fields):
        res[name] = value
    return res


def check_data_is_valid(line):
    '''
    Checks whether or not line is valid RLCS data. 
    If it is, returns True. If not, returns False.
    A valid line looks like W[xxxx]R where xxxx are data bytes.
    The line must also begin with W and end with R. 
    '''

    if len(line) != 2 + struct.calcsize(STRUCT_FMT):
        print("Warning: Format of data {} is wrong. Expected {} characters, got {}".format(
            line, struct.calcsize(STRUCT_FMT), len(line)))
        return False
        # In the future, we may want to extract information from the message despite poor formatting

    if line[0] != ord('W') or line[-1] != ord('R'):
        print("Warning: Data {} is invalid (must end with R and begin with W)".format(line))
        return False

    return True
