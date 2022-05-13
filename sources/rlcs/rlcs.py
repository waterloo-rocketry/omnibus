import time
from message_types import msg_index


def fmt_line(parsed_data):
    msg_type = parsed_data['msg_type']
    time_stamp = parsed_data['timestamp']
    data = parsed_data["data"]
    res = f"[ {msg_type} {time_stamp} ]"
    for k, v in data.items():
        res += f"   {k}: {v}"
    return res


def parse_rlcs(line):
    res = {}
    # timestamp and msg_type
    res["msg_type"] = "rlcs"
    res["timestamp"] = time.time() # the format is just raw time.time()
    res["data"] = {}
    # items
    for i, s in enumerate(msg_index):
        res["data"][s] = int(line[4*i:4*i+4], base=16)  # 4 chars for each keyword
    return res
