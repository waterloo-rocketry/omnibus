import pandas as pd
import os
import datetime

from typing import List, Any

def save_data_to_csv(file_path: str, data_df: pd.DataFrame):
    """Save the export data in our given format to a csv file, and return the size of the file"""

    formatted_can_size = "N/A"
    with open(file_path, "w") as outfile:
        data_df.to_csv(outfile, index=False)
        export_size = os.path.getsize(file_path)
        formatted_can_size = "{:.2f} MB".format(export_size / (1024 * 1024))
    return formatted_can_size

def save_manifest(manifest_args: dict):
    """Prepare and save a manifest file for the export, with the given arguments."""

    if "file_path" not in manifest_args:
        raise ValueError("Manifest must have a file path")
    
    manifest_empty_filler = "NONE"

    # The string literal must be un-indented to save properly
    manifest_text = f"""Data exported from {manifest_args.get("file_path", manifest_empty_filler)} with mode {manifest_args.get("mode", manifest_empty_filler)} and time range {manifest_args.get("start", manifest_empty_filler)} to {manifest_args.get("stop", manifest_empty_filler)}, exported at {datetime.datetime.now()} with the export hash {manifest_args.get("export_hash", manifest_empty_filler)}.
Exported columns:
DAQ: {manifest_args.get("daq_cols", manifest_empty_filler)}
CAN: {manifest_args.get("can_cols", manifest_empty_filler)}
Exported files:
DAQ: {manifest_args.get("daq_export_path", manifest_empty_filler)} ({manifest_args.get("formatted_daq_size", manifest_empty_filler)})
CAN: {manifest_args.get("can_export_path", manifest_empty_filler)} ({manifest_args.get("formatted_can_size", manifest_empty_filler)})
DAQ export settings:
Compression: {manifest_args.get("daq_compression", manifest_empty_filler)}
Aggregation function: {manifest_args.get("daq_aggregate_function", manifest_empty_filler)}
CAN entries were filterd for stricly {manifest_args.get("msg_packed_filtering", manifest_empty_filler)} timestamps, so may not be complete.
    """

    manifest_path = f"{manifest_args.get('file_path', 'NONE').replace('.log','')}_export_{manifest_args.get('export_hash', 'NONE')}_manifest.txt"

    with open(manifest_path, "w") as manifest_file:
        manifest_file.write(manifest_text)
