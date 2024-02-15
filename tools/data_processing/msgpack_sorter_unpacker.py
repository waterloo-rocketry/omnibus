import msgpack


# FIXME: this method is an intermediary hack, and instead each board's real time should be determined based off the message's wrapped timestamp, ignorning the msgpacked timestamp. See https://waterloorocketry.slack.com/archives/C07MX0QDS/p1706481412008559?thread_ts=1706479899.045329&cid=C07MX0QDS
def msgpackFilterUnpacker(infile, mode="behind_stream"):
    """A function to unpack msgpack data, and then filter it to ensure timestamps are only increasing. Used to filter a second delayed source of messages in the same file."""
    # unpack all messages
    all_messages = []
    for data in msgpack.Unpacker(infile):
        all_messages.append(data)

    print(f"Processing msgpacked messages in mode {mode}")

    # discard all messages if the current time is lower than running current time, by not adding them to the filtered and output list
    if mode == "ahead_stream":
        filtered_messages = []
        curr_max_time = 0
        for i in range(len(all_messages) - 1):
            if all_messages[i][1] >= curr_max_time:
                filtered_messages.append(all_messages[i])
                curr_max_time = all_messages[i][1]

        return filtered_messages

    elif mode == "behind_stream":
        # find all the messages that are higher than the current running time, and then actually discard the ones ahead and only keep the ones behind
        filtered_messages = []
        curr_max_time = 0
        for i in range(len(all_messages) - 1):
            if all_messages[i][1] >= curr_max_time:
                curr_max_time = all_messages[i][1]
            else:
                filtered_messages.append(all_messages[i])

        return filtered_messages

    else:
        return all_messages
