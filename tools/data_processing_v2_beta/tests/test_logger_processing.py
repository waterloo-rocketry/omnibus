import sys

from sources.parsley.main import FileCommunicator

import os
import tempfile
import pytest
from unittest.mock import patch
from tools.data_processing_v2_beta.processors.logger_processing import LoggerDataProcessor

class DummyFileCommunicator(FileCommunicator):
    def __init__(self, pages):
        self.pages = pages
        self.index = 0
    def read(self):
        if self.index < len(self.pages):
            page = self.pages[self.index]
            self.index += 1
            return page
        return b""

@pytest.fixture
def temp_csv_file():
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    yield path
    os.remove(path)

@patch("tools.data_processing_v2_beta.processors.logger_processing.parsley")
def test_process_success(mock_parsley, temp_csv_file):
    # Mock parsley.parse_logger to yield logs
    mock_parsley.parse_logger.return_value = iter([
        ("sid1", b"data1"),
        ("sid2", b"data2"),
    ])
    # Mock parsley.parse to return expected dicts
    mock_parsley.parse.side_effect = [
        {
            "board_type_id": "GPS",
            "board_inst_id": "ROCKET",
            "msg_prio": "HIGH",
            "msg_type": "GPS_LATITUDE",
            "data": {"time": 1.794, "other": [1.0, 2.0]},
        },
        {
            "board_type_id": "TELEMETRY",
            "board_inst_id": "GROUND",
            "msg_prio": "MEDIUM",
            "msg_type": "SENSOR_ANALOG",
            "data": {"time": 2.505, "other": [3.0, 4.0]},
        },
    ]
    communicator = DummyFileCommunicator([b"page1"])
    processor = LoggerDataProcessor(communicator)
    processor.process(temp_csv_file)
    # Check output file exists and has correct header
    with open(temp_csv_file, "r") as f:
        lines = f.readlines()
    assert len(lines) == 3  # Header + 2 data lines
    assert "Timestamp (ns) +- 10ns,board_type_id,board_inst_id,msg_prio,msg_type,data" == lines[0].strip()
    assert "1.794,GPS,ROCKET,HIGH,GPS_LATITUDE" == lines[1].strip()
    assert "2.505,TELEMETRY,GROUND,MEDIUM,SENSOR_ANALOG" == lines[2].strip()

@patch("tools.data_processing_v2_beta.processors.logger_processing.parsley")
def test_process_empty_log(mock_parsley, temp_csv_file):
    mock_parsley.parse_logger.return_value = None
    communicator = DummyFileCommunicator([b"page1"])
    processor = LoggerDataProcessor(communicator)
    processor.process(temp_csv_file)
    with open(temp_csv_file, "r") as f:
        lines = f.readlines()
    assert len(lines) == 1  # Only header
    assert "Timestamp (ns) +- 10ns,board_type_id,board_inst_id,msg_prio,msg_type,data" == lines[0].strip()

@patch("tools.data_processing_v2_beta.processors.logger_processing.parsley")
def test_process_malformed_data(mock_parsley, temp_csv_file):
    mock_parsley.parse_logger.return_value = iter([("sid1", b"data1")])
    mock_parsley.parse.return_value = None  # Malformed data
    communicator = DummyFileCommunicator([b"page1"])
    processor = LoggerDataProcessor(communicator)
    processor.process(temp_csv_file)
    with open(temp_csv_file, "r") as f:
        lines = f.readlines()
    assert len(lines) == 1  # Only header
    assert "Timestamp (ns) +- 10ns,board_type_id,board_inst_id,msg_prio,msg_type,data" == lines[0].strip()
