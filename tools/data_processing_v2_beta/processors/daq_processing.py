# pyright: strict

import csv
import os
import msgpack
from io import BufferedReader
from typing import cast, TypedDict
from dataclasses import dataclass
from collections import deque
import sys

MESSAGE_FORMAT_VERSION = 2

DAQ_EXPECTED_RECEIVE_DATA_FORMAT = {
    "timestamp": float,
    "data": dict,  # data is actually dict[str, list[float]]
    "relative_timestamps_nanoseconds": list,  # actually list[int]
    "sample_rate": int,
    "message_format_version": int,
}


@dataclass(frozen=True)
class DAQ_RECEIVED_MESSAGE_TYPE(TypedDict):
    timestamp: float
    data: dict[str, list[float]]
    """    
    Each sensor groups a certain number of readings, the bulk read rate of the DAQ.
    The length of that list corresponds to the length of relative_timestamps_nanoseconds below.
    The floating point numbers are arbitrary values depending on the unit of the sensor configured when it was recorded.
    """
    # Example: {
    #     "NPT-201: Nitrogen Fill PT (psi)": [1.3, 2.3, 4.3],
    #     "OPT-201: Ox Fill PT (psi)": [2.3, 4.5, 7.2],
    #     ...
    # }
    # 1.3 and 2.3 are the readings for each sensor at t0, 2.3 and 4.5 for t1, etc.

    relative_timestamps_nanoseconds: list[int]
    """
    Corresponding timestamps for each reading of every sensors, calculated from sample rate (dt_ns = 1/sample_rate * 10^9).
    There can be variation of +- 1ns for every point, according to NI box data sheet, which is minimal.
    Timestamps are based on initial time t_0 = time.time_ns(), meaning they should be always unique.
    Unit is nanoseconds
    """
    # Example: [19, 22, 25] <- 1.3 and 2.3 from above was read at t0 = 19

    # Rate at which the messages were read, in Hz, dt = 1/sample_rate
    sample_rate: int

    # Arbitrary constant that validates that the received message format is compatible
    # Increment MESSAGE_FORMAT_VERSION both here and in the NI source whenever the structure changes
    message_format_version: int


@dataclass(frozen=True)
class DAQDataStructure:
    daq_box_timestamp: float  # System timestamp from DAQ box, not used for processing
    ni_relative_timestamp: int  # In nanoseconds
    sensors: list[str]
    values: list[float]


class DAQDataProcessor:

    _all_available_sensors: list[str] = []
    _log_file_stream: BufferedReader
    _expected_channel: str
    # So we can pop as we process entries since log messages are first-in-first-out
    _unprocessed_datapoints: deque[DAQ_RECEIVED_MESSAGE_TYPE]
    processed_data: deque[DAQDataStructure] | None = None

    def __init__(
        self, log_file_stream: BufferedReader, daq_channel: str = "DAQ"
    ) -> None:
        self._log_file_stream = log_file_stream
        self._expected_channel = daq_channel
        self._unprocessed_datapoints = deque()

    # TODO: Unpack onto disk rather than into RAM, reduces possibility of OOM error
    def process(self):
        """
        Begin data processing. Blocking call.
        """
        self._unpack()
        self._expand_and_structure_all_datapoints()

    def _unpack(self) -> None:
        """Unpack msgpacked globallog containing DAQ data"""

        unpacker = msgpack.Unpacker(
            self._log_file_stream  # pyright: ignore[reportArgumentType]
        )

        for msg in unpacker:
            # Assuming the globallog is not corrupted, this should be true
            assert type(msg) is list
            msg = cast(list[float | str | DAQ_RECEIVED_MESSAGE_TYPE], msg)

            # Example ["DAQ", 12345.02, {data here}]
            assert len(msg) == 3
            assert type(msg[0]) is str
            assert type(msg[1]) is float
            assert type(msg[2]) is dict

            channel, _, unpacked_data = cast(
                tuple[str, float, DAQ_RECEIVED_MESSAGE_TYPE], tuple(msg)
            )

            if channel != self._expected_channel:
                continue

            # Verify the message version
            if ("message_format_version" not in unpacked_data) or (
                unpacked_data["message_format_version"] != MESSAGE_FORMAT_VERSION
            ):
                raise AssertionError(
                    "[FATAL] [DAQ Unpacker] This version of data processing is not compatible with the DAQ messages provided!"
                )

            # Verify that the unpacked_data is actually valid
            for key in DAQ_EXPECTED_RECEIVE_DATA_FORMAT.keys():
                if key not in unpacked_data:
                    print(
                        f"[WARN] [DAQ Unpacker] Malformed Line! '{str(unpacked_data)}'",
                        file=sys.stderr,
                    )
                    continue
                # Cast to object to check that item's type
                if (
                    type(cast(object, unpacked_data[key]))
                    != DAQ_EXPECTED_RECEIVE_DATA_FORMAT[key]
                ):
                    print(
                        f"[WARN] [DAQ Unpacker] Malformed Line! '{str(unpacked_data)}'",
                        file=sys.stderr,
                    )
                    continue

            self._unprocessed_datapoints.append(unpacked_data)

    def _expand_and_structure_datapoint(
        self, unprocessed_datapoint: DAQ_RECEIVED_MESSAGE_TYPE
    ) -> list[DAQDataStructure]:
        """
        Expand single unprocessed datapoints, containing a grouping of datapoints
        into a list of single datapoints.
        """
        sensors = list(unprocessed_datapoint["data"].keys())
        results: list[DAQDataStructure] = []
        for i, timestamp in enumerate(
            unprocessed_datapoint["relative_timestamps_nanoseconds"]
        ):
            # The index of the timestamp array corresponds to the index of the sensor reading that was taken at that point in time
            # Value at given timestamp for the sensor at the corresponding index in the sensors array
            sensor_values: list[float] = []
            for sensor in sensors:
                sensor_values.append(unprocessed_datapoint["data"][sensor][i])

            processed_point = DAQDataStructure(
                unprocessed_datapoint["timestamp"], timestamp, sensors, sensor_values
            )
            results.append(processed_point)
        return results

    def _expand_and_structure_all_datapoints(self) -> None:
        """
        Expand all datapoints in self._unprocessed_datapoints, popping as we go through the queue.
        """
        self.processed_data = deque()
        while self._unprocessed_datapoints:
            unprocessed_datapoint = self._unprocessed_datapoints.popleft()
            expanded_points = self._expand_and_structure_datapoint(
                unprocessed_datapoint
            )
            for p in expanded_points:
                self.processed_data.append(p)

    def csv_ify(self, file_path: str) -> str:
        """
        Create CSV file from unpacked DAQ data.
        The first column will always be the timestamp in nanoseconds
        """
        assert self.processed_data  # Make sure we have processed the data
        formatted_can_size = "N/A"
        # TODO: Make this better (dynamic column creation, select which cols, etc.)
        with open(file_path, "w") as outfile:
            writer = csv.writer(outfile)
            writer.writerow(["Timestamp (ns) +- 10ns"] + self.processed_data[0].sensors)
            for datapoint in self.processed_data:
                writer.writerow([datapoint.ni_relative_timestamp] + datapoint.values)
            export_size = os.path.getsize(file_path)
            formatted_can_size = "{:.2f} MB".format(export_size / (1024 * 1024))
        return formatted_can_size
