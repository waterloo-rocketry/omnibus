import time
from rlcs_message_config import msg_index


def fmt_line(parsed_data):
    msg_type = parsed_data['msg_type']
    time_stamp = parsed_data['timestamp']
    data = parsed_data["data"]
    res = f"[ {msg_type} {time_stamp} ]"
    for k, v in data.items():
        res += f"   {k}: {v}"
    return res


def parse_rlcs(line):
    line = line[1:len(line)-1]
    res = {}
    # timestamp and msg_type
    res["msg_type"] = "rlcs"
    res["timestamp"] = time.time()
    res["data"] = {}
    # items
    for i, s in enumerate(msg_index):
        res["data"][s] = int(line[4*i:4*i+4], base=16)  # 4 chars for each keyword
    return res


def check_invalid_data(line):
    is_valid = True
    # check if line is in a valid input format
    if line[0] != "W" or line[len(line)-1] != "R":
        is_valid = False
        print("Data " + line + " is invalid (must end with R and begin with W")

    if len(line) != 34:
        is_valid = False
        print("Warning: Format {} is wrong. Expected 34 characters, got {}".format(line, len(line)))
        # In the future, we may want to extract information from the message despite poor formatting

    for i in range(1, len(line)-1):
        if line[i] not in "abcdef0123456789":
            is_valid = False
            print("Error: Expected hexadecimal numbers, got {} at index {}".format(line[i], i))

    return is_valid
