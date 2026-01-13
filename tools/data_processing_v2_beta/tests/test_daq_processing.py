import pytest
import msgpack
from io import BytesIO, StringIO
from data_processing_v2_beta.processors.daq_processing import (
    DAQDataProcessor,
    MESSAGE_FORMAT_VERSION,
)


class TestValidateAndExtractData:

    @pytest.fixture
    def processor(self):
        buff = BytesIO(b"")
        return DAQDataProcessor(log_file_stream=buff)

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
            "INVALID",  # Not DAQ Message type
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
                "message_format_version": 0,  # Wrong version
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
                # Missing sensor data
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
                # Missing sensor timestamps
                "sample_rate": 1,
                "message_format_version": MESSAGE_FORMAT_VERSION,
            },
        ]
        result = processor.validate_and_extract_data(invalid)
        assert result is None


class TestUnpackAndStreamToCSV:

    def test_normal_processing_creates_csv(self):
        messages = [
            ["DAQ", 1234.0, {
                "timestamp": 1234.0,
                "data": {"sensor1": [1.1, 1.2], "sensor2": [2.1, 2.2]},
                "relative_timestamps_nanoseconds": [100, 200],
                "sample_rate": 1,
                "message_format_version": MESSAGE_FORMAT_VERSION,
            }]
        ]

        stream = BytesIO()
        for msg in messages:
            stream.write(msgpack.packb(msg))
        stream.seek(0)

        processor = DAQDataProcessor(log_file_stream=stream)

        buf = StringIO()
        processor.unpack_and_stream_to_csv(buf)

        lines = buf.getvalue().splitlines()

        assert lines[0] == "Timestamp (ns) +- 10ns,sensor1,sensor2"
        assert lines[1] == "100,1.1,2.1"
        assert lines[2] == "200,1.2,2.2"

    def test_empty_message_creates_empty_csv(self):
        stream = BytesIO()
        processor = DAQDataProcessor(log_file_stream=stream)

        buf = StringIO()
        processor.unpack_and_stream_to_csv(buf)

        assert buf.getvalue() == ""  # empty csv

    def test_malformed_message_skipped(self):
        bad_messages = [
            ["DAQ", 1234.0, {
                "timestamp": 1234.0,
                "message_format_version": MESSAGE_FORMAT_VERSION
            }],
            ["DAQ", 1234.0, {
                "timestamp": 1234.0,
                "data": {"sensor1": [1.1], "sensor2": [2.1]},
                "relative_timestamps_nanoseconds": [100],
                "sample_rate": 1,
                "message_format_version": MESSAGE_FORMAT_VERSION,
            }],
        ]

        stream = BytesIO()
        for msg in bad_messages:
            stream.write(msgpack.packb(msg))
        stream.seek(0)

        processor = DAQDataProcessor(log_file_stream=stream)

        buf = StringIO()
        processor.unpack_and_stream_to_csv(buf)

        lines = buf.getvalue().splitlines()

        assert lines[0] == "Timestamp (ns) +- 10ns,sensor1,sensor2"
        assert lines[1] == "100,1.1,2.1"


def test_multiple_valid_messages():
    msgs = [
        ["DAQ", 0.0, {
            "timestamp": 0.0,
            "data": {"s": [1]},
            "relative_timestamps_nanoseconds": [100],
            "sample_rate": 1,
            "message_format_version": MESSAGE_FORMAT_VERSION,
        }],
        ["DAQ", 0.0, {
            "timestamp": 0.0,
            "data": {"s": [2]},
            "relative_timestamps_nanoseconds": [200],
            "sample_rate": 1,
            "message_format_version": MESSAGE_FORMAT_VERSION,
        }],
    ]

    stream = BytesIO()
    for m in msgs:
        stream.write(msgpack.packb(m))
    stream.seek(0)

    processor = DAQDataProcessor(log_file_stream=stream)

    buf = StringIO()
    processor.unpack_and_stream_to_csv(buf)

    lines = buf.getvalue().splitlines()

    assert lines == [
        "Timestamp (ns) +- 10ns,s",
        "100,1",
        "200,2",
    ]


def test_inconsistent_sensor_lengths():
    msg = ["DAQ", 0.0, {
        "timestamp": 0.0,
        "data": {"sensor 1": [1, 2], "sensor 2": [10]},  # inconsistent
        "relative_timestamps_nanoseconds": [100, 200],
        "sample_rate": 1,
        "message_format_version": MESSAGE_FORMAT_VERSION,
    }]

    stream = BytesIO()
    stream.write(msgpack.packb(msg))
    stream.seek(0)

    processor = DAQDataProcessor(log_file_stream=stream)

    buf = StringIO()
    with pytest.raises(ValueError):
        processor.unpack_and_stream_to_csv(buf)
