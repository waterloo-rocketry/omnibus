import message_types as mt

# external library for parsing

def fmt_line(parsed_data):
    msg_type = parsed_data['msg_type']
    time_stamp = parsed_data['timestamp']
    data = parsed_data["data"]
    res = f"[ {msg_type} {time_stamp} ]"
    for k, v in data.items():
        res += f"   {k}: {v}"
    return res