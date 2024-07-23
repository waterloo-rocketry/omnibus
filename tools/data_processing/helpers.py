from typing import List, Union
import pandas as pd

def offset_timestamps(dataframes: List[Union[pd.DataFrame, None]]) -> int:
    """Offset the timestamps of the data sources so that they start at 0, and return the time offset that was applied. If a data source is empty (None), it will be ignored."""
    
    # Find the minimum timestamp across all non-empty dataframes
    min_timestamps = [df["timestamp"].min() for df in dataframes if df is not None]
    if not min_timestamps:
        raise ValueError("All data sources are empty, can't offset timestamps.")
    time_offset = min(min_timestamps)
    
    # Adjust the timestamps in each non-empty dataframe
    for df in dataframes:
        if df is not None:
            df["timestamp"] -= time_offset

    return time_offset


def filter_timestamps(data: Union[pd.DataFrame, None], start: float, stop: float):
    """Filter the data to only include the timestamps between start and stop, in place"""
    if data is not None:
        return  data[(data["timestamp"] >= start) & (data["timestamp"] <= stop)]
    else:
        return None
