import pytest
import msgpack
from io import BytesIO, StringIO

from tools.data_processing_v2_beta.processors.daq_processing import (
    DAQDataProcessor,
    DAQDataProcessor_V3,
    DAQHostSyncProcessor_V3,
)
from tools.data_processing_v2_beta.processors.message_types import (
    MESSAGE_FORMAT_VERSION,
    MESSAGE_FORMAT_VERSION_V3,
)

def pack_messages(*messages: object) -> BytesIO:
    stream = BytesIO()
    for message in messages:
        _ = stream.write(msgpack.packb(message))
    _ = stream.seek(0)
    return stream

# V2 tests

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


def test_auto_detects_first_v2_daq_source_and_skips_alternates(capsys):
    msgs = [
        ["DAQ/ni", 0.0, {
            "timestamp": 0.0,
            "data": {"s": [1]},
            "relative_timestamps_nanoseconds": [100],
            "sample_rate": 1,
            "message_format_version": MESSAGE_FORMAT_VERSION,
        }],
        ["DAQ/ljm", 0.0, {
            "timestamp": 0.0,
            "data": {"s": [2]},
            "relative_timestamps_nanoseconds": [200],
            "sample_rate": 1,
            "message_format_version": MESSAGE_FORMAT_VERSION,
        }],
        ["DAQ/ni", 0.0, {
            "timestamp": 0.0,
            "data": {"s": [3]},
            "relative_timestamps_nanoseconds": [300],
            "sample_rate": 1,
            "message_format_version": MESSAGE_FORMAT_VERSION,
        }],
    ]

    stream = BytesIO()
    for msg in msgs:
        stream.write(msgpack.packb(msg))
    stream.seek(0)

    processor = DAQDataProcessor(log_file_stream=stream)

    buf = StringIO()
    processor.unpack_and_stream_to_csv(buf)

    lines = buf.getvalue().splitlines()
    stderr = capsys.readouterr().err

    assert lines == [
        "Timestamp (ns) +- 10ns,s",
        "100,1",
        "300,3",
    ]
    assert "alternate DAQ source 'DAQ/ljm'" in stderr


def test_explicit_v2_daq_source_filters_other_sources():
    msgs = [
        ["DAQ/ni", 0.0, {
            "timestamp": 0.0,
            "data": {"s": [1]},
            "relative_timestamps_nanoseconds": [100],
            "sample_rate": 1,
            "message_format_version": MESSAGE_FORMAT_VERSION,
        }],
        ["DAQ/ljm", 0.0, {
            "timestamp": 0.0,
            "data": {"s": [2]},
            "relative_timestamps_nanoseconds": [200],
            "sample_rate": 1,
            "message_format_version": MESSAGE_FORMAT_VERSION,
        }],
    ]

    stream = BytesIO()
    for msg in msgs:
        stream.write(msgpack.packb(msg))
    stream.seek(0)

    processor = DAQDataProcessor(log_file_stream=stream, daq_channel="DAQ/ljm")

    buf = StringIO()
    processor.unpack_and_stream_to_csv(buf)

    assert buf.getvalue().splitlines() == [
        "Timestamp (ns) +- 10ns,s",
        "200,2",
    ]

# V3 tests

class TestValidateAndExtractData_V3:

    @pytest.fixture
    def processor(self):
        buff = BytesIO(b"")
        return DAQDataProcessor_V3(log_file_stream=buff)

    def test_valid_message_returns_data(self, processor):
        valid_message = [
            "DAQ",
            1234.0,
            {
                "timestamp": 123.0,
                "data": {"sensor1": [1, 2], "sensor2": [1, 2]},
                "relative_timestamps": [0.0000001, 0.0000002],
                "sample_rate": 1,
                "message_format_version": MESSAGE_FORMAT_VERSION_V3,
            },
        ]
        result = processor.validate_and_extract_data(valid_message)
        assert result is not None
        assert result == valid_message[2]

    def test_valid_message_with_integer_timestamps_returns_data(self, processor):
        valid_message = [
            "DAQ",
            1234.0,
            {
                "timestamp": 123.0,
                "data": {"sensor1": [1, 2], "sensor2": [1, 2]},
                "relative_timestamps": [1, 2],
                "sample_rate": 1,
                "message_format_version": MESSAGE_FORMAT_VERSION_V3,
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
                "relative_timestamps": [0.0000001, 0.0000002],
                "sample_rate": 1,
                "message_format_version": MESSAGE_FORMAT_VERSION_V3,
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
                "relative_timestamps": [0.0000001, 0.0000002],
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
                "relative_timestamps": [0.0000001, 0.0000002],
                "sample_rate": 1,
                "message_format_version": MESSAGE_FORMAT_VERSION_V3,
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
                "message_format_version": MESSAGE_FORMAT_VERSION_V3,
            },
        ]
        result = processor.validate_and_extract_data(invalid)
        assert result is None


class TestUnpackAndStreamToCSV_V3:

    def test_normal_processing_creates_csv(self):
        messages = [
            ["DAQ", 1234.0, {
                "timestamp": 1234.0,
                "data": {"sensor1": [1.1, 1.2], "sensor2": [2.1, 2.2]},
                "relative_timestamps": [0.0000001, 0.0000002],
                "sample_rate": 1,
                "message_format_version": MESSAGE_FORMAT_VERSION_V3,
            }]
        ]

        stream = BytesIO()
        for msg in messages:
            stream.write(msgpack.packb(msg))
        stream.seek(0)

        processor = DAQDataProcessor_V3(log_file_stream=stream)

        buf = StringIO()
        processor.unpack_and_stream_to_csv(buf)

        lines = buf.getvalue().splitlines()

        assert lines[0] == "Timestamp (s),sensor1,sensor2"
        assert lines[1] == "1e-07,1.1,2.1"
        assert lines[2] == "2e-07,1.2,2.2"

    def test_empty_message_creates_empty_csv(self):
        stream = BytesIO()
        processor = DAQDataProcessor_V3(log_file_stream=stream)

        buf = StringIO()
        processor.unpack_and_stream_to_csv(buf)

        assert buf.getvalue() == ""  # empty csv

    def test_malformed_message_skipped(self):
        bad_messages = [
            ["DAQ", 1234.0, {
                "timestamp": 1234.0,
                "message_format_version": MESSAGE_FORMAT_VERSION_V3
            }],
            ["DAQ", 1234.0, {
                "timestamp": 1234.0,
                "data": {"sensor1": [1.1], "sensor2": [2.1]},
                "relative_timestamps": [0.0000001],
                "sample_rate": 1,
                "message_format_version": MESSAGE_FORMAT_VERSION_V3,
            }],
        ]

        stream = BytesIO()
        for msg in bad_messages:
            stream.write(msgpack.packb(msg))
        stream.seek(0)

        processor = DAQDataProcessor_V3(log_file_stream=stream)

        buf = StringIO()
        processor.unpack_and_stream_to_csv(buf)

        lines = buf.getvalue().splitlines()

        assert lines[0] == "Timestamp (s),sensor1,sensor2"
        assert lines[1] == "1e-07,1.1,2.1"


def test_multiple_valid_messages_v3():
    msgs = [
        ["DAQ", 0.0, {
            "timestamp": 0.0,
            "data": {"s": [1]},
            "relative_timestamps": [0.0000001],
            "sample_rate": 1,
            "message_format_version": MESSAGE_FORMAT_VERSION_V3,
        }],
        ["DAQ", 0.0, {
            "timestamp": 0.0,
            "data": {"s": [2]},
            "relative_timestamps": [0.0000002],
            "sample_rate": 1,
            "message_format_version": MESSAGE_FORMAT_VERSION_V3,
        }],
    ]

    stream = BytesIO()
    for m in msgs:
        stream.write(msgpack.packb(m))
    stream.seek(0)

    processor = DAQDataProcessor_V3(log_file_stream=stream)

    buf = StringIO()
    processor.unpack_and_stream_to_csv(buf)

    lines = buf.getvalue().splitlines()

    assert lines == [
        "Timestamp (s),s",
        "1e-07,1",
        "2e-07,2",
    ]


def test_inconsistent_sensor_lengths_v3():
    msg = ["DAQ", 0.0, {
        "timestamp": 0.0,
        "data": {"sensor 1": [1, 2], "sensor 2": [10]},  # inconsistent
        "relative_timestamps": [0.0000001, 0.0000002],
        "sample_rate": 1,
        "message_format_version": MESSAGE_FORMAT_VERSION_V3,
    }]

    stream = BytesIO()
    stream.write(msgpack.packb(msg))
    stream.seek(0)

    processor = DAQDataProcessor_V3(log_file_stream=stream)

    buf = StringIO()
    with pytest.raises(ValueError):
        processor.unpack_and_stream_to_csv(buf)


def test_auto_detects_first_v3_daq_source_and_skips_alternates(capsys):
    msgs = [
        ["DAQ/ni", 0.0, {
            "timestamp": 0.0,
            "data": {"s": [1]},
            "relative_timestamps": [0.0000001],
            "sample_rate": 1,
            "message_format_version": MESSAGE_FORMAT_VERSION_V3,
        }],
        ["DAQ/ljm", 0.0, {
            "timestamp": 0.0,
            "data": {"s": [2]},
            "relative_timestamps": [0.0000002],
            "sample_rate": 1,
            "message_format_version": MESSAGE_FORMAT_VERSION_V3,
        }],
        ["DAQ/ni", 0.0, {
            "timestamp": 0.0,
            "data": {"s": [3]},
            "relative_timestamps": [0.0000003],
            "sample_rate": 1,
            "message_format_version": MESSAGE_FORMAT_VERSION_V3,
        }],
    ]

    stream = BytesIO()
    for msg in msgs:
        stream.write(msgpack.packb(msg))
    stream.seek(0)

    processor = DAQDataProcessor_V3(log_file_stream=stream)

    buf = StringIO()
    processor.unpack_and_stream_to_csv(buf)

    lines = buf.getvalue().splitlines()
    stderr = capsys.readouterr().err

    assert lines == [
        "Timestamp (s),s",
        "1e-07,1",
        "3e-07,3",
    ]
    assert "alternate DAQ source 'DAQ/ljm'" in stderr


def test_explicit_v3_daq_source_filters_other_sources():
    msgs = [
        ["DAQ/ni", 0.0, {
            "timestamp": 0.0,
            "data": {"s": [1]},
            "relative_timestamps": [0.0000001],
            "sample_rate": 1,
            "message_format_version": MESSAGE_FORMAT_VERSION_V3,
        }],
        ["DAQ/ljm", 0.0, {
            "timestamp": 0.0,
            "data": {"s": [2]},
            "relative_timestamps": [0.0000002],
            "sample_rate": 1,
            "message_format_version": MESSAGE_FORMAT_VERSION_V3,
        }],
    ]

    stream = BytesIO()
    for msg in msgs:
        stream.write(msgpack.packb(msg))
    stream.seek(0)

    processor = DAQDataProcessor_V3(log_file_stream=stream, daq_channel="DAQ/ljm")

    buf = StringIO()
    processor.unpack_and_stream_to_csv(buf)

    assert buf.getvalue().splitlines() == [
        "Timestamp (s),s",
        "2e-07,2",
    ]


def test_host_sync_recomputes_single_source_timestamps():
    processor = DAQHostSyncProcessor_V3(
        log_file_stream=pack_messages(
            ["DAQ/ni", 500.0, {
                "timestamp": 5.0,
                "data": {"ni_pressure": [100.0, 101.0]},
                "relative_timestamps": [0.00, 0.01],
                "sample_rate": 100,
                "message_format_version": MESSAGE_FORMAT_VERSION_V3,
            }],
            ["DAQ/ni", 1000.0, {
                "timestamp": 10.0,
                "data": {"ni_pressure": [102.0, 103.0]},
                "relative_timestamps": [0.02, 0.03],
                "sample_rate": 100,
                "message_format_version": MESSAGE_FORMAT_VERSION_V3,
            }],
            ["DAQ/ni", 1400.0, {
                "timestamp": 14.0,
                "data": {"ni_pressure": [104.0, 105.0]},
                "relative_timestamps": [0.04, 0.05],
                "sample_rate": 100,
                "message_format_version": MESSAGE_FORMAT_VERSION_V3,
            }],
        ),
        daq_channel="DAQ/ni",
    )

    buf = StringIO()
    processor.unpack_and_stream_to_csv(buf)

    assert buf.getvalue().splitlines() == [
        "Timestamp (s),Source,ni_pressure",
        "5.0,DAQ/ni,102.0",
        "7.25,DAQ/ni,103.0",
        "9.5,DAQ/ni,104.0",
        "11.75,DAQ/ni,105.0",
    ]


def test_host_sync_merges_all_sources_in_timestamp_order():
    processor = DAQHostSyncProcessor_V3(
        log_file_stream=pack_messages(
            ["DAQ/ni", 100.0, {
                "timestamp": 1.0,
                "data": {"ni_pressure": [1.0]},
                "relative_timestamps": [0.0],
                "sample_rate": 10,
                "message_format_version": MESSAGE_FORMAT_VERSION_V3,
            }],
            ["DAQ/ljm", 150.0, {
                "timestamp": 1.5,
                "data": {"ljm_temp": [20.0]},
                "relative_timestamps": [0.0],
                "sample_rate": 10,
                "message_format_version": MESSAGE_FORMAT_VERSION_V3,
            }],
            ["DAQ/ni", 200.0, {
                "timestamp": 2.0,
                "data": {"ni_pressure": [2.0, 3.0]},
                "relative_timestamps": [0.1, 0.2],
                "sample_rate": 10,
                "message_format_version": MESSAGE_FORMAT_VERSION_V3,
            }],
            ["DAQ/ljm", 250.0, {
                "timestamp": 2.5,
                "data": {"ljm_temp": [21.0]},
                "relative_timestamps": [0.1],
                "sample_rate": 10,
                "message_format_version": MESSAGE_FORMAT_VERSION_V3,
            }],
            ["DAQ/ni", 400.0, {
                "timestamp": 4.0,
                "data": {"ni_pressure": [4.0, 5.0]},
                "relative_timestamps": [0.3, 0.4],
                "sample_rate": 10,
                "message_format_version": MESSAGE_FORMAT_VERSION_V3,
            }],
            ["DAQ/ljm", 450.0, {
                "timestamp": 4.5,
                "data": {"ljm_temp": [22.0]},
                "relative_timestamps": [0.2],
                "sample_rate": 10,
                "message_format_version": MESSAGE_FORMAT_VERSION_V3,
            }],
        )
    )

    buf = StringIO()
    processor.unpack_and_stream_to_csv(buf)

    assert buf.getvalue().splitlines() == [
        "Timestamp (s),Source,ljm_temp,ni_pressure",
        "1.0,DAQ/ni,,2.0",
        "1.5,DAQ/ljm,21.0,",
        "1.75,DAQ/ni,,3.0",
        "2.5,DAQ/ni,,4.0",
        "3.0,DAQ/ljm,22.0,",
        "3.25,DAQ/ni,,5.0",
    ]


def test_host_sync_filters_to_one_explicit_source():
    processor = DAQHostSyncProcessor_V3(
        log_file_stream=pack_messages(
            ["DAQ/ni", 100.0, {
                "timestamp": 1.0,
                "data": {"ni_pressure": [1.0]},
                "relative_timestamps": [0.0],
                "sample_rate": 10,
                "message_format_version": MESSAGE_FORMAT_VERSION_V3,
            }],
            ["DAQ/ljm", 200.0, {
                "timestamp": 2.0,
                "data": {"ljm_temp": [20.0]},
                "relative_timestamps": [0.0],
                "sample_rate": 10,
                "message_format_version": MESSAGE_FORMAT_VERSION_V3,
            }],
            ["DAQ/ni", 300.0, {
                "timestamp": 3.0,
                "data": {"ni_pressure": [2.0]},
                "relative_timestamps": [0.1],
                "sample_rate": 10,
                "message_format_version": MESSAGE_FORMAT_VERSION_V3,
            }],
            ["DAQ/ni", 500.0, {
                "timestamp": 5.0,
                "data": {"ni_pressure": [3.0]},
                "relative_timestamps": [0.2],
                "sample_rate": 10,
                "message_format_version": MESSAGE_FORMAT_VERSION_V3,
            }],
        ),
        daq_channel="DAQ/ni",
    )

    buf = StringIO()
    processor.unpack_and_stream_to_csv(buf)

    assert buf.getvalue().splitlines() == [
        "Timestamp (s),Source,ni_pressure",
        "1.0,DAQ/ni,2.0",
        "3.0,DAQ/ni,3.0",
    ]


def test_host_sync_raises_when_source_has_only_one_message():
    processor = DAQHostSyncProcessor_V3(
        log_file_stream=pack_messages(
            ["DAQ/ni", 1.0, {
                "timestamp": 1.0,
                "data": {"ni_pressure": [1.0]},
                "relative_timestamps": [0.0],
                "sample_rate": 10,
                "message_format_version": MESSAGE_FORMAT_VERSION_V3,
            }]
        )
    )

    with pytest.raises(ValueError, match="does not have enough message blocks"):
        processor.unpack_and_stream_to_csv(StringIO())


def test_host_sync_raises_on_non_positive_elapsed_time():
    processor = DAQHostSyncProcessor_V3(
        log_file_stream=pack_messages(
            ["DAQ/ni", 1.0, {
                "timestamp": 2.0,
                "data": {"ni_pressure": [1.0]},
                "relative_timestamps": [0.0],
                "sample_rate": 10,
                "message_format_version": MESSAGE_FORMAT_VERSION_V3,
            }],
            ["DAQ/ni", 2.0, {
                "timestamp": 2.0,
                "data": {"ni_pressure": [2.0]},
                "relative_timestamps": [0.1],
                "sample_rate": 10,
                "message_format_version": MESSAGE_FORMAT_VERSION_V3,
            }],
            ["DAQ/ni", 2.0, {
                "timestamp": 2.0,
                "data": {"ni_pressure": [3.0]},
                "relative_timestamps": [0.2],
                "sample_rate": 10,
                "message_format_version": MESSAGE_FORMAT_VERSION_V3,
            }],
        ),
        daq_channel="DAQ/ni",
    )

    with pytest.raises(ValueError, match="non-positive host time span"):
        processor.unpack_and_stream_to_csv(StringIO())


def test_host_sync_raises_on_mismatched_sensor_lengths():
    processor = DAQHostSyncProcessor_V3(
        log_file_stream=pack_messages(
            ["DAQ/ni", 1.0, {
                "timestamp": 1.0,
                "data": {"ni_pressure": [1.0]},
                "relative_timestamps": [0.0],
                "sample_rate": 10,
                "message_format_version": MESSAGE_FORMAT_VERSION_V3,
            }],
            ["DAQ/ni", 2.0, {
                "timestamp": 2.0,
                "data": {"ni_pressure": [2.0, 3.0], "ni_temp": [10.0]},
                "relative_timestamps": [0.1, 0.2],
                "sample_rate": 10,
                "message_format_version": MESSAGE_FORMAT_VERSION_V3,
            }],
            ["DAQ/ni", 3.0, {
                "timestamp": 3.0,
                "data": {"ni_pressure": [4.0, 5.0], "ni_temp": [11.0, 12.0]},
                "relative_timestamps": [0.3, 0.4],
                "sample_rate": 10,
                "message_format_version": MESSAGE_FORMAT_VERSION_V3,
            }],
        ),
        daq_channel="DAQ/ni",
    )

    with pytest.raises(ValueError, match="Mismatched sensor data lengths"):
        processor.unpack_and_stream_to_csv(StringIO())
