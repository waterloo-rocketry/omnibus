import csv
import os
from dataclasses import dataclass
from typing import TypedDict, Any

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
    def __init__(self, log_file_reader: Any):
        self._log_file_reader = log_file_reader
        self.MASTER_COLUMNS = [
            #  Metadata 
            'time', 
            'logger_time',
            'msg_prio', 
            'board_type_id', 
            'board_inst_id', 
            'msg_type',
            
            #  Primary Data
            'pressure', 
            'temp', 
            'imu_id',
            'linear_accel', 
            'angular_velocity', 
            'mag',
            
            # GPS Data 
            'hrs', 'mins', 'secs', 'dsecs',        # Time
            'degs', 'dmins', 'direction',          # Location
            'altitude', 'daltitude', 'unit',       # Vertical
            'num_sats', 'quality',                 # Health
            
            #  Actuators & Power 
            'actuator', 
            'curr_state', 
            'req_state',
            'sensor_id', 
            'value',
            
            # System Health & Errors 
            'general_error_bitfield', 
            'board_error_bitfield'
        ]
        # Preprocessed dict for quick lookup
        self.column_to_idx = {name: i for i, name in enumerate(self.MASTER_COLUMNS)}


    def _flatten_message(self, parsed_entry: list) -> dict[str, Any]:
        """
        Input: ['CAN/Parsley', 1746896240.8, {'board_type_id': 'PROCESSOR', ..., 'data': {'mag': 65479}}]
        Output: {'board_type_id': 'PROCESSOR', 'mag': 65479, ...}
        """
        raw_dict = parsed_entry[2]
        
        flat_msg = raw_dict.copy()
        
        if 'data' in flat_msg:
            payload = flat_msg.pop('data')  
            flat_msg.update(payload)
            
        return flat_msg

    def _map_to_csv_row(self, parsley_output: list) -> list:
        unix_logger_time = parsley_output[1]
        flattened_data = self._flatten_message(parsley_output)

        row = [""] * len(self.MASTER_COLUMNS)

        if 'logger_time' in self.column_to_idx:
            row[self.column_to_idx['logger_time']] = unix_logger_time

        for key, value in flattened_data.items():
            if key in self.column_to_idx:
                index = self.column_to_idx[key]
                row[index] = value
            
        return row
       

    def process_log_and_write_csv(self, output_file: str, parsed_messages: list):
        with open(output_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(self.MASTER_COLUMNS)

            for msg in parsed_messages:
                row = self._map_to_csv_row(msg)
                writer.writerow(row)

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



