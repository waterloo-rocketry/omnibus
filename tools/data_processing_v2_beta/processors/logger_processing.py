import csv
import os
from dataclasses import dataclass
from typing import TypedDict

import parsley
from sources.parsley.main import FileCommunicator

LOGGER_EXPECTED_RECEIVE_DATA_FORMAT = {
    "board_type_id": str,
    "board_inst_id": str,
    "msg_prio": str,
    "msg_type": str,
    "data": dict[str, list[float]],
}

class LoggerDataProcessor:
    def __init__(self, log_file_reader):
        self._log_file_reader = log_file_reader
        self.master_columns = [
            'time', 'board_type_id', 'msg_type', 
            'pressure', 'temp', 'value', 'latitude' #add more values
        ]

    def _flatten(self, parsed_entry: list) -> dict[str, Any]:
        pass

    def _map_dict_to_row(self, flat_data: dict) -> list:
        
        row = [""] * len(self.master_columns)

       
        for key, value in flat_data.items():
            if key in self.master_columns:
               
                index = self.master_columns.index(key)
                
                row[index] = value
        
        return row

    def process_and_write(self, output_file, parsed_messages):
        with open(output_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(self.master_columns)

            for msg in parsed_messages:
                flat = self._flatten(msg) 
    
                manual_row = self._map_dict_to_row(flat)
            
                writer.writerow(manual_row)

# class LoggerDataProcessor:
#     _log_file_reader: FileCommunicator

#     def __init__(self, log_file_reader: FileCommunicator) -> None:
#         self._log_file_reader = log_file_reader

#     def process(self, output_file_path: str) -> str:
#         """
#         Begin data processing. Blocking call.
#         """
#         return self._unpack_and_stream_to_csv(output_file_path)


#     def _unpack_and_stream_to_csv(self, output_file_path: str) -> str:
#         with (open(output_file_path, "w", newline="") as outfile):
#             writer = csv.writer(outfile)
#             writer.writerow(["Timestamp (ns) +- 10ns"] + list(LOGGER_EXPECTED_RECEIVE_DATA_FORMAT.keys()))

#             page_number = 0
#             while (page := self._log_file_reader.read()) != b"":
#                 log_generator = parsley.parse_logger(page, page_number)
#                 page_number += 1
#                 if log_generator is None:
#                     continue

#                 while (log := next(log_generator, None)) is not None:
#                     msg_sid, msg_data = log
#                     parsed_data = parsley.parse(msg_sid, msg_data)
#                     if parsed_data is None:
#                         continue

#                     # split off time
#                     time = parsed_data["data"].pop("time", 0)

#                     writer.writerow([time] + list(parsed_data.values()))

#         export_size = os.path.getsize(output_file_path)
#         return "{:.2f} MB".format(export_size / (1024 * 1024))



