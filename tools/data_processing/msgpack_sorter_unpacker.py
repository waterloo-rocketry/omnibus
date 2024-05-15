import msgpack

from typing import IO

# FIXME: this method is an intermediary hack, and instead each board's real time should be determined based off the message's wrapped timestamp, ignorning the msgpacked timestamp. See https://waterloorocketry.slack.com/archives/C07MX0QDS/p1706481412008559?thread_ts=1706479899.045329&cid=C07MX0QDS


def msgpackFilterUnpacker(infile: IO, mode="behind_stream"):
    """A function to unpack msgpack data, and then filter it to ensure timestamps are only increasing. Used to filter a second delayed source of messages in the same file."""

    # unpack all messages
    all_messages = []
    for data in msgpack.Unpacker(infile):
        all_messages.append(data)

    print(f"Processing msgpacked messages in mode {mode}")

    # discard all messages if the current time is lower than running current time, by not adding them to the filtered and output list
    filtered_messages = []
    curr_max_time = 0
    for i in range(len(all_messages) - 1):
        if mode == "ahead_stream":
            if all_messages[i][1] >= curr_max_time:
                filtered_messages.append(all_messages[i])
                curr_max_time = all_messages[i][1]
        elif mode == "behind_stream":   # find all the messages that are higher than the current running time, and then actually discard the ones ahead and only keep the ones behind
            if all_messages[i][1] >= curr_max_time:
                curr_max_time = all_messages[i][1]
            else:
                filtered_messages.append(all_messages[i])
        else:
            raise ValueError(f"Unknown msgpack filter mode {mode}")

    return filtered_messages
