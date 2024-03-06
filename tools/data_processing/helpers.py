def offset_timestamps(data1, data2):
    """Offset the timestamps of the two data sources so that they start at 0, and return the time offset that was applied to both data sources."""
    # we need logic to handle the case where one of the data sources is empty, becuase a recording might only have CAN data
    if len(data1) > 0 and len(data2) > 0:
        time_offset = min(data1[0][0], data2[0][0])
    elif len(data1) > 0:
        time_offset = data1[0][0]
    elif len(data2) > 0:
        time_offset = data2[0][0]
    else:
        raise ValueError("Both data sources are empty, can't offset timestamps.")

    for i in range(len(data1)):
        data1[i][0] -= time_offset
    for i in range(len(data2)):
        data2[i][0] -= time_offset

    return time_offset


def filter_timestamps(data, start, stop):
    """Filter the data to only include the timestamps between start and stop"""
    return [d for d in data if d[0] >= start and d[0] <= stop]

