import csv
import os

from typing import List, Any


def save_data_to_csv(file_path: str, data: List[Any], cols: List[str]):
    """Save the export data in our given format to a csv file, and return the size of the file"""

    formatted_can_size = "N/A"
    with open(file_path, "w") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(["time"] + cols)
        for line in data:
            writer.writerow(line)
        export_size = os.path.getsize(file_path)
        formatted_can_size = "{:.2f} MB".format(export_size / (1024 * 1024))
    return formatted_can_size
