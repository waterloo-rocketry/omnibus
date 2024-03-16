from typing import List, Any, Union
import pandas as pd

def offset_timestamps(data1: Union[pd.DataFrame,None], data2: Union[pd.DataFrame,None]) -> int:
    """Offset the timestamps of the two data sources so that they start at 0, and return the time offset that was applied to both data sources. If the data source is empty (None), it will be ignored."""
    
    # we need logic to handle the case where one of the data sources is empty, becuase a recording might only have CAN data
    if data1 is not None and data2 is not None:
        time_offset = min(data1["timestamp"].min(), data2["timestamp"].min())
    elif data1 is not None:
        time_offset = data1["timestamp"].min()
    elif data2 is not None:
        time_offset = data2["timestamp"].min()
    else:
        raise ValueError("Both data sources are empty, can't offset timestamps.")

    if data1 is not None:
        data1["timestamp"] -= time_offset
    if data2 is not None:
        data2["timestamp"] -= time_offset

    return time_offset


def filter_timestamps(data: Union[pd.DataFrame, None], start: float, stop: float):
    """Filter the data to only include the timestamps between start and stop, in place"""
    if data is not None:
        return  data[(data["timestamp"] >= start) & (data["timestamp"] <= stop)]
    else:
        return None

