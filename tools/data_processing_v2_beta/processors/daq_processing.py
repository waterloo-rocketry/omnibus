# pyright: strict

import csv
import heapq
import msgpack
import os
import sys
import tempfile
from collections.abc import Iterator
from contextlib import ExitStack
from dataclasses import dataclass
from itertools import count
from typing import BinaryIO, Generic, TextIO, cast

from .message_types import (
    DAQFormatConfig,
    DAQReceivedMessageV2,
    DAQReceivedMessageV3,
    PayloadT,
    V2_FORMAT,
    V3_FORMAT,
)

DAQ_CHANNEL_PREFIX = "DAQ/"
LEGACY_DAQ_CHANNEL = "DAQ"


@dataclass(frozen=True)
class ValidatedDAQMessage(Generic[PayloadT]):
    channel: str
    host_timestamp: float
    payload: PayloadT


@dataclass(frozen=True)
class HostSyncSampleRow:
    timestamp: float
    source: str
    sensor_values: dict[str, float]


@dataclass
class SpoolState:
    file: BinaryIO
    saw_initial_message: bool = False
    kept_message_count: int = 0
    total_samples: int = 0
    start_timestamp: float | None = None
    end_timestamp: float | None = None


def is_daq_channel(channel: str) -> bool:
    return channel == LEGACY_DAQ_CHANNEL or channel.startswith(DAQ_CHANNEL_PREFIX)

class BaseDAQProcessor(Generic[PayloadT]):
    _log_file_stream: BinaryIO
    _expected_channel: str | None
    _auto_detect_channel: bool
    _warned_alternate_channels: set[str]
    _format: DAQFormatConfig[PayloadT]

    def __init__(
        self,
        log_file_stream: BinaryIO,
        daq_channel: str | None,
        message_format: DAQFormatConfig[PayloadT],
    ) -> None:
        self._log_file_stream = log_file_stream
        self._expected_channel = daq_channel
        self._auto_detect_channel = daq_channel is None
        self._warned_alternate_channels = set()
        self._format = message_format

    def _is_daq_channel(self, channel: str) -> bool:
        return is_daq_channel(channel)

    def _should_process_channel(self, channel: str) -> bool:
        if not self._is_daq_channel(channel):
            return False

        if self._expected_channel is None:
            self._expected_channel = channel
            return True

        if channel == self._expected_channel:
            return True

        if self._auto_detect_channel and channel not in self._warned_alternate_channels:
            print(
                f"[WARN] [DAQ Unpacker] Detected alternate DAQ source '{channel}' while processing '{self._expected_channel}'. Skipping messages from the alternate source.",
                file=sys.stderr,
            )
            self._warned_alternate_channels.add(channel)

        return False

    def process(self, output_file_path: str) -> str:
        with open(output_file_path, "w", newline="") as outfile:
            self.unpack_and_stream_to_csv(outfile)

        export_size = os.path.getsize(output_file_path)
        return "{:.2f} MB".format(export_size / (1024 * 1024))

    def _validate_payload(self, payload: object) -> PayloadT | None:
        if not isinstance(payload, dict):
            return None

        unpacked_data = cast(PayloadT, cast(object, payload))

        if (
            "message_format_version" not in unpacked_data
            or unpacked_data["message_format_version"] != self._format.message_format_version
        ):
            raise AssertionError(
                "[FATAL] [DAQ Unpacker] This version of data processing is not compatible with the DAQ messages provided!"
            )

        for key, expected_type in self._format.expected_data_shape.items():
            if key not in unpacked_data or not isinstance(unpacked_data[key], expected_type):
                print(
                    f"[WARN] [DAQ Unpacker] Malformed Line! '{str(unpacked_data)}'",
                    file=sys.stderr,
                )
                return None

        return unpacked_data

    def validate_payload(self, payload: object) -> PayloadT | None:
        return self._validate_payload(payload)

    def validate_and_extract_data(
        self, msg: list[float | str | PayloadT]
    ) -> PayloadT | None:
        validated = self.validate_and_extract_message(cast(list[object], msg))
        if validated is None:
            return None
        return validated.payload

    def validate_and_extract_message(
        self, msg: list[object]
    ) -> ValidatedDAQMessage[PayloadT] | None:
        assert len(msg) == 3
        assert type(msg[0]) is str
        assert type(msg[1]) is float
        assert type(msg[2]) is dict

        channel, host_timestamp, payload = cast(tuple[str, float, object], tuple(msg))

        if not self._should_process_channel(channel):
            return None

        unpacked_data = self._validate_payload(payload)
        if unpacked_data is None:
            return None

        return ValidatedDAQMessage(
            channel=channel,
            host_timestamp=host_timestamp,
            payload=unpacked_data,
        )

    def _iter_validated_messages(self) -> Iterator[ValidatedDAQMessage[PayloadT]]:
        unpacker = msgpack.Unpacker(self._log_file_stream)

        for msg in unpacker:
            if not isinstance(msg, list):
                continue

            msg_list = cast(list[object], msg)
            validated = self.validate_and_extract_message(msg_list)
            if validated is not None:
                yield validated

    def _sample_count(self, payload: PayloadT) -> int:
        timestamp_field = self._format.timestamp_field
        if timestamp_field == "relative_timestamps_nanoseconds":
            return len(cast(DAQReceivedMessageV2, payload)["relative_timestamps_nanoseconds"])
        return len(cast(DAQReceivedMessageV3, payload)["relative_timestamps"])

    def _sample_timestamps(self, payload: PayloadT) -> list[int] | list[int | float]:
        timestamp_field = self._format.timestamp_field
        if timestamp_field == "relative_timestamps_nanoseconds":
            return cast(DAQReceivedMessageV2, payload)["relative_timestamps_nanoseconds"]
        return cast(DAQReceivedMessageV3, payload)["relative_timestamps"]

    def _validate_sensor_lengths(
        self, payload: PayloadT, sensors: list[str] | None = None
    ) -> None:
        sample_count = self._sample_count(payload)
        sensor_names = sensors or list(payload["data"].keys())

        for sensor in sensor_names:
            sensor_values = payload["data"].get(sensor)
            if sensor_values is None:
                raise ValueError(f"Missing sensor '{sensor}' in DAQ message")
            if len(sensor_values) != sample_count:
                raise ValueError("Mismatched sensor data lengths")

    def unpack_and_stream_to_csv(self, outfile: TextIO) -> None:
        writer = csv.writer(outfile)
        wrote_header = False
        sensors: list[str] = []

        for message in self._iter_validated_messages():
            payload = message.payload

            if not wrote_header:
                sensors = sorted(payload["data"].keys())
                writer.writerow([self._format.timestamp_header] + sensors)
                wrote_header = True

            self._validate_sensor_lengths(payload, sensors)

            timestamps = self._sample_timestamps(payload)
            for index, timestamp in enumerate(timestamps):
                writer.writerow(
                    [timestamp] + [payload["data"][sensor][index] for sensor in sensors]
                )


class DAQDataProcessor(BaseDAQProcessor[DAQReceivedMessageV2]):
    def __init__(self, log_file_stream: BinaryIO, daq_channel: str | None = None) -> None:
        super().__init__(log_file_stream, daq_channel, V2_FORMAT)


class DAQDataProcessor_V3(BaseDAQProcessor[DAQReceivedMessageV3]):
    def __init__(self, log_file_stream: BinaryIO, daq_channel: str | None = None) -> None:
        super().__init__(log_file_stream, daq_channel, V3_FORMAT)


class DAQHostSyncProcessor_V3:
    _log_file_stream: BinaryIO
    _selected_channel: str | None

    def __init__(self, log_file_stream: BinaryIO, daq_channel: str | None = None) -> None:
        self._log_file_stream = log_file_stream
        self._selected_channel = daq_channel

    def process(self, output_file_path: str) -> str:
        with open(output_file_path, "w", newline="") as outfile:
            self.unpack_and_stream_to_csv(outfile)

        export_size = os.path.getsize(output_file_path)
        return "{:.2f} MB".format(export_size / (1024 * 1024))

    def _iter_selected_messages(self) -> Iterator[ValidatedDAQMessage[DAQReceivedMessageV3]]:
        unpacker = msgpack.Unpacker(self._log_file_stream)
        validator = DAQDataProcessor_V3(self._log_file_stream, daq_channel=self._selected_channel)

        for msg in unpacker:
            if not isinstance(msg, list):
                continue

            msg_list = cast(list[object], msg)
            assert len(msg_list) == 3
            assert isinstance(msg_list[0], str)
            assert isinstance(msg_list[1], float)
            assert isinstance(msg_list[2], dict)

            channel = msg_list[0]
            host_timestamp = msg_list[1]
            payload = cast(object, msg_list[2])

            if not is_daq_channel(channel):
                continue

            if self._selected_channel is not None and channel != self._selected_channel:
                continue

            unpacked_data = validator.validate_payload(payload)
            if unpacked_data is None:
                continue

            yield ValidatedDAQMessage(channel=channel, host_timestamp=host_timestamp, payload=unpacked_data)

    def _spool_messages(
        self, stack: ExitStack
    ) -> tuple[list[str], dict[str, SpoolState]]:
        source_states: dict[str, SpoolState] = {}
        all_sensors: set[str] = set()

        for message in self._iter_selected_messages():
            all_sensors.update(message.payload["data"].keys())
            state = source_states.get(message.channel)
            if state is None:
                state = SpoolState(file=stack.enter_context(tempfile.TemporaryFile()))
                source_states[message.channel] = state

            if not state.saw_initial_message:
                state.saw_initial_message = True
                state.start_timestamp = message.payload["timestamp"]
                continue

            sample_count = len(message.payload["relative_timestamps"])
            for sensor_values in message.payload["data"].values():
                if len(sensor_values) != sample_count:
                    raise ValueError("Mismatched sensor data lengths")

            state.end_timestamp = message.payload["timestamp"]
            state.total_samples += sample_count
            state.kept_message_count += 1

            _ = msgpack.pack(
                [message.channel, message.payload["timestamp"], message.payload],
                state.file,
            )

        return sorted(all_sensors), source_states

    def _iter_host_sync_rows(
        self, source: str, state: SpoolState
    ) -> Iterator[HostSyncSampleRow]:
        if state.kept_message_count == 0 or state.start_timestamp is None or state.end_timestamp is None:
            raise ValueError(
                f"DAQ source '{source}' does not have enough message blocks for host sync; need at least 2 blocks so the first can be discarded"
            )

        elapsed_host_time = state.end_timestamp - state.start_timestamp
        if elapsed_host_time <= 0:
            raise ValueError(
                f"DAQ source '{source}' has non-positive host time span for host sync"
            )

        if state.total_samples <= 0:
            raise ValueError(
                f"DAQ source '{source}' does not contain any samples after host-sync priming discard"
            )

        true_sample_rate = state.total_samples / elapsed_host_time
        sample_index = 0
        state.file.seek(0)
        unpacker = msgpack.Unpacker(state.file)

        for spooled_message in unpacker:
            if not isinstance(spooled_message, list):
                continue

            spooled_message_list = cast(list[object], spooled_message)
            assert len(spooled_message_list) == 3
            assert isinstance(spooled_message_list[0], str)
            assert isinstance(spooled_message_list[1], float)
            assert isinstance(spooled_message_list[2], dict)
            channel = spooled_message_list[0]
            payload_timestamp = spooled_message_list[1]
            payload = cast(DAQReceivedMessageV3, cast(object, spooled_message_list[2]))
            assert channel == source

            sample_count = len(payload["relative_timestamps"])
            for index in range(sample_count):
                timestamp = state.start_timestamp + (sample_index / true_sample_rate)
                assert payload_timestamp >= state.start_timestamp
                yield HostSyncSampleRow(
                    timestamp=timestamp,
                    source=source,
                    sensor_values={
                        sensor_name: sensor_values[index]
                        for sensor_name, sensor_values in payload["data"].items()
                    },
                )
                sample_index += 1

    def unpack_and_stream_to_csv(self, outfile: TextIO) -> None:
        writer = csv.writer(outfile)
        with ExitStack() as stack:
            sensors, source_states = self._spool_messages(stack)
            if not source_states:
                return

            writer.writerow(["Timestamp (s)", "Source"] + sensors)

            heap: list[tuple[float, str, int, HostSyncSampleRow, Iterator[HostSyncSampleRow]]] = []
            tiebreaker = count()

            for source, state in source_states.items():
                row_iterator = self._iter_host_sync_rows(source, state)
                try:
                    first_row = next(row_iterator)
                except StopIteration:
                    continue
                heapq.heappush(
                    heap,
                    (
                        first_row.timestamp,
                        first_row.source,
                        next(tiebreaker),
                        first_row,
                        row_iterator,
                    ),
                )

            while heap:
                _, _, _, row, row_iterator = heapq.heappop(heap)
                writer.writerow(
                    [row.timestamp, row.source]
                    + [row.sensor_values.get(sensor, "") for sensor in sensors]
                )
                try:
                    next_row = next(row_iterator)
                except StopIteration:
                    continue
                heapq.heappush(
                    heap,
                    (
                        next_row.timestamp,
                        next_row.source,
                        next(tiebreaker),
                        next_row,
                        row_iterator,
                    ),
                )
