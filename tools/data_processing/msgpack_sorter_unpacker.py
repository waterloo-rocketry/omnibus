import msgpack

def msgpackSorterUnpacker(infile): # FIXME: this method should not be used, and instead each board's real time should be determined, ignorning the msgpacked timestamp. See https://waterloorocketry.slack.com/archives/C07MX0QDS/p1706481412008559?thread_ts=1706479899.045329&cid=C07MX0QDS
    all_messages = []
    for data in msgpack.Unpacker(infile):
        all_messages.append(data)

    # discard all messages if the current time is lower than running current time
    skips = set()
    curr_max_time = 0
    for i in range(len(all_messages) - 1):
        if all_messages[i][1] < curr_max_time:
            skips.add(i)
        else:
            curr_max_time = all_messages[i][1]

    skipped_messages = []
    for i in range(len(all_messages)):
        if i not in skips:
            skipped_messages.append(all_messages[i])

    return skipped_messages
