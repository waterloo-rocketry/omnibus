import pytest
import msgpack
from io import BufferedReader, BytesIO
from data_processing_v2_beta.processors.daq_processing import (
    DAQDataProcessor,
    MESSAGE_FORMAT_VERSION,

)
 
class TestValidateAndExtractData:

    @pytest.fixture
    def processor(self):
        buff = BytesIO(b'')
        return DAQDataProcessor(log_file_stream=BufferedReader(buff))
    
    def test_valid_message_returns_data(self, processor):
        valid_message = [
        "DAQ",
        1234.0,
        {
            "timestamp": 123.0,
            "data": {"sensor1": [1, 2], "sensor2": [1, 2]},
            "relative_timestamps_nanoseconds": [100, 200],
            "sample_rate": 1,
            "message_format_version": MESSAGE_FORMAT_VERSION,
        },
        ]
        result = processor.validate_and_extract_data(valid_message)
        assert result is not None
        assert result == valid_message[2]

    def test_wrong_channel_returns_none(self, processor):
        invalid = [
        "INVALID", #Not DAQ Message type
        1234.0,
        {
            "timestamp": 123.0,
            "data": {"sensor1": [1, 2], "sensor2": [1, 2]},
            "relative_timestamps_nanoseconds": [100, 200],
            "sample_rate": 1,
            "message_format_version": MESSAGE_FORMAT_VERSION,
        },
    ]
        result = processor.validate_and_extract_data(invalid)
        assert result is None

    def test_wrong_message_version_raises_assertion(self, processor):
        invalid = [
        "DAQ",
        1234.0,
        {
            "timestamp": 123.0,
            "data": {"sensor1": [1, 2], "sensor2": [1, 2]},
            "relative_timestamps_nanoseconds": [100, 200],
            "sample_rate": 1,
            "message_format_version": 0, #Wrong version
        },
    ]
        with pytest.raises(AssertionError):
            processor.validate_and_extract_data(invalid)

    def test_missing_keys_returns_none(self, processor):

        invalid = [
        "DAQ",
        1234.0,
        {
            "timestamp": 123.0,
            #Missing sensor data
            "relative_timestamps_nanoseconds": [100, 200],
            "sample_rate": 1,
            "message_format_version": MESSAGE_FORMAT_VERSION,
        },
    ]
        result = processor.validate_and_extract_data(invalid)
        assert result is None

        invalid = [
        "DAQ",
        1234.0,
        {
            "timestamp": 123.0,
            "data": {"sensor1": [1, 2], "sensor2": [1, 2]},
            #Missing sensor timestamps
            "sample_rate": 1,
            "message_format_version": MESSAGE_FORMAT_VERSION,
        },
    ]
        result = processor.validate_and_extract_data(invalid)
        assert result is None

@pytest.fixture
def temp_csv_file(tmp_path):
    path = tmp_path / "output.csv" # type: ignore
    return str(path)

@pytest.fixture
def dummy_log_stream(valid_message):
    stream = BytesIO()
    stream.write(msgpack.packb(valid_message))
    stream.seek(0)
    return stream

@pytest.fixture
def processor(dummy_log_stream):
    return DAQDataProcessor(log_file_stream=dummy_log_stream)


class TestUnpackAndStreamToCSV:
    
    def test_normal_processing_creates_csv(self, temp_csv_file):
        messages = [
            ["DAQ", 1234.0, {
                "timestamp": 1234.0,
                "data": {"sensor1": [1.1, 1.2], "sensor2": [2.1, 2.2]},
                "relative_timestamps_nanoseconds": [100, 200],
                "sample_rate": 1,
                "message_format_version": MESSAGE_FORMAT_VERSION
            }]
        ]
        stream = BytesIO()
        for msg in messages:
            stream.write(msgpack.packb(msg))
        stream.seek(0)        
        processor = DAQDataProcessor(log_file_stream=BufferedReader(stream))
        processor.unpack_and_stream_to_csv(temp_csv_file)
        
        with open(temp_csv_file, "r") as f:
            lines = f.readlines()

        assert lines[0].strip() == "Timestamp (ns) +- 10ns,sensor1,sensor2"
        assert lines[1].strip() == "100,1.1,2.1"
        assert lines[2].strip() == "200,1.2,2.2"

    def test_empty_message_creates_empty_csv(self, temp_csv_file):
        stream = BytesIO()

        processor = DAQDataProcessor(log_file_stream=BufferedReader(stream))
        processor.unpack_and_stream_to_csv(temp_csv_file)
        with open(temp_csv_file, 'r') as f:
            lines = f.readlines()
        
        assert lines == [] #empty csv

    def test_malformed_message_skipped(self, temp_csv_file):
        bad_message = [
            ["DAQ", 1234.0, {"timestamp": 1234.0, "message_format_version": MESSAGE_FORMAT_VERSION}], 
            #bad message contains two DAQ lists, only one is properly formatted
            ["DAQ", 1234.0, {
                "timestamp": 1234.0,
                "data": {"sensor1": [1.1], "sensor2": [2.1]},
                "relative_timestamps_nanoseconds": [100],
                "sample_rate": 1,
                "message_format_version": MESSAGE_FORMAT_VERSION
            }]
        ]

        stream = BytesIO()
        for msg in bad_message:
            stream.write(msgpack.packb(msg))
        stream.seek(0)

        processor = DAQDataProcessor(log_file_stream=BufferedReader(stream))
        processor.unpack_and_stream_to_csv(temp_csv_file)
        with open(temp_csv_file, 'r') as f:
            lines = f.readlines()
        
        assert lines[0].strip() == "Timestamp (ns) +- 10ns,sensor1,sensor2"
        assert lines[1].strip() == "100,1.1,2.1"

def test_multiple_valid_messages(temp_csv_file):
    msgs = [
        ["DAQ", 0.0, {
            "timestamp": 0.0,
            "data": {"s": [1]},
            "relative_timestamps_nanoseconds": [100],
            "sample_rate": 1,
            "message_format_version": MESSAGE_FORMAT_VERSION
        }],
        ["DAQ", 0.0, {
            "timestamp": 0.0,
            "data": {"s": [2]},
            "relative_timestamps_nanoseconds": [200],
            "sample_rate": 1,
            "message_format_version": MESSAGE_FORMAT_VERSION
        }],
    ]

    stream = BytesIO()
    for m in msgs:
        stream.write(msgpack.packb(m))
    stream.seek(0)

    processor = DAQDataProcessor(log_file_stream=BufferedReader(stream))
    processor.unpack_and_stream_to_csv(temp_csv_file)

    with open(temp_csv_file) as f:
        lines = [l.strip() for l in f.readlines()]

    assert lines == [
        "Timestamp (ns) +- 10ns,s",
        "100,1",
        "200,2",
    ]


def test_inconsistent_sensor_lengths(temp_csv_file):
    msg = ["DAQ", 0.0, {
        "timestamp": 0.0,
        "data": {"sensor 1": [1, 2], "sensor 2": [10]},  # inconsistent
        "relative_timestamps_nanoseconds": [100, 200],
        "sample_rate": 1,
        "message_format_version": MESSAGE_FORMAT_VERSION
    }]

    stream = BytesIO()
    stream.write(msgpack.packb(msg))
    stream.seek(0)

    processor = DAQDataProcessor(log_file_stream=BufferedReader(stream))

    with pytest.raises(Exception):
        processor.unpack_and_stream_to_csv(temp_csv_file)
