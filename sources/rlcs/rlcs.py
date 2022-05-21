from config import MSG_INDEX


def fmt_line(parsed_data):
    msg_type = parsed_data['msg_type']
    data = parsed_data["data"]
    res = f"[ {msg_type} ]"
    for k, v in data.items():
        res += f"   {k}: {v}"
    return res


def parse_rlcs(line):
    '''parses data as well as checks for data validity 
        returns none if data is invalid 
    '''
    if not check_data_is_valid(line):
        return None

    line = line[1:len(line)-1]
    res = {}
    # timestamp and msg_type
    res["msg_type"] = "rlcs"
    res["data"] = {}
    # items
    for i, s in enumerate(MSG_INDEX):
        res["data"][s] = int(line[4*i:4*i+4], base=16)  # 4 chars for each keyword
    return res


def check_data_is_valid(line):
    '''
    Checks whether or not line is valid RLCS data. 
    If it is, returns True. If not, returns False.
    A valid line looks like W[xxxx][xxxx]...[xxxx]R where xxxx = a hexadecimal number, 
    with one hexadecimal number corresponding to each value in MSG_INDEX. 
    The line must also begin with W and end with R. 
    '''

    if len(line) != 4*len(MSG_INDEX)+2:
        print("Warning: Format of data {} is wrong. Expected {} characters, got {}".format(
            line, 4*len(MSG_INDEX)+2, len(line)))
        return False
        # In the future, we may want to extract information from the message despite poor formatting

    if line[0].lower() != "w" or line[len(line)-1].lower() != "r":
        print("Warning: Data {} is invalid (must end with R and begin with W)".format(line))
        return False

    for c in line[1:len(line)-1]:
        if c.lower() not in "abcdef0123456789":
            print(
                "Warning: Invalid hex data {}".format(line))
            return False

    return True
