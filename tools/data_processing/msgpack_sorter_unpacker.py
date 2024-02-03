import msgpack

def msgpackFilterUnpacker(infile): # FIXME: this method should not be used, and instead each board's real time should be determined, ignorning the msgpacked timestamp. See https://waterloorocketry.slack.com/archives/C07MX0QDS/p1706481412008559?thread_ts=1706479899.045329&cid=C07MX0QDS
    """A function to unpack msgpack data, and then filter it to ensure timestamps are only increasing. Used to filter a second delayed source of messages in the same file."""
    # unpack all messages
    all_messages = []
    for data in msgpack.Unpacker(infile):
        all_messages.append(data)

    # discard all messages if the current time is lower than running current time, by not adding them to the filtered and output list
    filtered_messages = []
    curr_max_time = 0
    for i in range(len(all_messages) - 1):
        if all_messages[i][1] >= curr_max_time:
            filtered_messages.append(all_messages[i])
            curr_max_time = all_messages[i][1]

    return filtered_messages