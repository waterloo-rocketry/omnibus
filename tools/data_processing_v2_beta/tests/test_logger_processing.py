import csv
import json
import pytest
from io import StringIO


from tools.data_processing_v2_beta.processors.logger_processing import LoggerDataProcessor


class FakeMessage:
   def __init__(self, data: dict):
       self._data = data


   def to_flat_dict(self) -> dict:
       return self._data

@pytest.fixture
def processor():
   return LoggerDataProcessor()

@pytest.fixture
def sample_messages():
   return [
       (
           "sid1",
           1.0,
           FakeMessage(
               {
                   "msg_prio": "HIGH",
                   "board_type_id": "GPS",
                   "board_inst_id": "ROCKET",
                   "msg_type": "GPS_LATITUDE",
                   "pressure": 101.1,
                   "temp": 20.0,
               }
           ),
       ),
       (
           "sid2",
           2.0,
           FakeMessage(
               {
                   "msg_prio": "MEDIUM",
                   "board_type_id": "TELEMETRY",
                   "board_inst_id": "GROUND",
                   "msg_type": "SENSOR_ANALOG",
                   "sensor_id": "S1",
                   "value": 110,
               }
           ),
       ),
   ]

def test_flatten_message_injects_logger_time(processor):
   msg = ("sid", 9.9, FakeMessage({"msg_prio": "HIGH"}))


   flat = processor._flatten_message(msg)


   assert flat["logger_time"] == 9.9
   assert flat["msg_prio"] == "HIGH"

def test_csv_header_is_correct(processor, sample_messages, tmp_path):
   path = tmp_path / "out.csv"


   processor.process_log_and_write_csv(str(path), sample_messages)


   with open(path, "r") as f:
       reader = csv.reader(f)
       header = next(reader)


   assert header == processor.MASTER_COLUMNS

def test_csv_row_mapping(processor, sample_messages, tmp_path):
   path = tmp_path / "out.csv"


   processor.process_log_and_write_csv(str(path), sample_messages)


   with open(path, "r") as f:
       rows = list(csv.reader(f))


   assert len(rows) == 3  # header + 2 rows


   idx = processor.column_to_idx


   # row 1
   assert rows[1][idx["msg_prio"]] == "HIGH"
   assert rows[1][idx["board_type_id"]] == "GPS"
   assert rows[1][idx["logger_time"]] == "1.0"

def test_json_output_matches_flattened_structure(processor, sample_messages, tmp_path):
   path = tmp_path / "out.json"


   processor.process_log_and_write_json(str(path), sample_messages)


   with open(path, "r") as f:
       lines = [line.strip() for line in f if line.strip()]
       data = [json.loads(line) for line in lines]


   assert len(data) == 2


   assert data[0]["msg_prio"] == "HIGH"
   assert data[0]["logger_time"] == 1.0
def test_unknown_fields_are_ignored(processor, tmp_path):
   msg = (
       "sid",
       1.0,
       FakeMessage({"unknown_field": 123, "msg_prio": "LOW"}),
   )


   path = tmp_path / "out.csv"
   processor.process_log_and_write_csv(str(path), [msg])


   with open(path, "r") as f:
       rows = list(csv.reader(f))


   assert len(rows) == 2
   assert "unknown_field" not in processor.column_to_idx

def test_missing_fields_do_not_crash(processor, tmp_path):
   msg = ("sid", 1.0, FakeMessage({}))


   path = tmp_path / "out.csv"
   processor.process_log_and_write_csv(str(path), [msg])


   with open(path, "r") as f:
       rows = list(csv.reader(f))


   assert len(rows) == 2  # header + row
   assert rows[1]  # row exists

def test_list_and_dict_serialization(processor, tmp_path):
   msg = (
       "sid",
       1.0,
       FakeMessage(
           {
               "msg_prio": "HIGH",
               "pressure": [1, 2, 3],
               "temp": {"a": 1},
           }
       ),
   )


   path = tmp_path / "out.csv"
   processor.process_log_and_write_csv(str(path), [msg])


   with open(path, "r") as f:
       rows = list(csv.reader(f))


   idx = processor.column_to_idx


   pressure = json.loads(rows[1][idx["pressure"]])
   temp = json.loads(rows[1][idx["temp"]])


   assert pressure == [1, 2, 3]
   assert temp == {"a": 1}

def test_empty_input_writes_only_header(processor, tmp_path):
   path = tmp_path / "out.csv"


   processor.process_log_and_write_csv(str(path), [])


   with open(path, "r") as f:
       rows = list(csv.reader(f))


   assert rows == [processor.MASTER_COLUMNS]

