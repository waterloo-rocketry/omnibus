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

class DAQDataProcessor:

    _all_available_sensors: list[str] = []
    _log_file_stream: BufferedReader
    _expected_channel: str
    # So we can pop as we process entries since log messages are first-in-first-out
    _unprocessed_datapoints: deque[DAQ_RECEIVED_MESSAGE_TYPE]

    def __init__(
        self, log_file_stream: BufferedReader, daq_channel: str = "DAQ"
    ) -> None:
        self._log_file_stream = log_file_stream
        self._expected_channel = daq_channel
        self._unprocessed_datapoints = deque()

    # TODO: Unpack onto disk rather than into RAM, reduces possibility of OOM error
    def process(self, output_file_path: str) -> str:
        """
        Begin data processing. Blocking call.
        """
        return self._unpack_and_stream_to_csv(output_file_path)
    
    def _validate_and_extract_data(self, msg: list[float | str | DAQ_RECEIVED_MESSAGE_TYPE]) -> DAQ_RECEIVED_MESSAGE_TYPE | None:

        # Example ["DAQ", 12345.02, {data here}]
        assert len(msg) == 3
        assert type(msg[0]) is str
        assert type(msg[1]) is float
        assert type(msg[2]) is dict

        channel, _, unpacked_data = cast(
            tuple[str, float, DAQ_RECEIVED_MESSAGE_TYPE], tuple(msg)
        )

        if channel != self._expected_channel:
            return None
        
        # Verify the message version
        if ("message_format_version" not in unpacked_data) or (
            unpacked_data["message_format_version"] != MESSAGE_FORMAT_VERSION
        ):
            raise AssertionError(
                "[FATAL] [DAQ Unpacker] This version of data processing is not compatible with the DAQ messages provided!"
            )

        # Verify that the unpacked_data is actually valid
        for key in DAQ_EXPECTED_RECEIVE_DATA_FORMAT:
            if key not in unpacked_data:
                print(
                    f"[WARN] [DAQ Unpacker] Malformed Line! '{str(unpacked_data)}'",
                    file=sys.stderr,
                )
                return None
            # Cast to object to check that item's type
            if not isinstance(
                unpacked_data[key], DAQ_EXPECTED_RECEIVE_DATA_FORMAT[key]
            ):
                print(
                    f"[WARN] [DAQ Unpacker] Malformed Line! '{str(unpacked_data)}'",
                    file=sys.stderr,
                )
                return None
        
        # If we reach here, the data is valid and can be returned.
        return unpacked_data

    def _unpack_and_stream_to_csv(self, output_file_path: str) -> str:

        with open(output_file_path, "w", newline="") as outfile:
            writer = csv.writer(outfile)
            
            unpacker = msgpack.Unpacker(
                self._log_file_stream  # pyright: ignore[reportArgumentType]
            )
            wrote_header_flag = False

            for msg in unpacker:
                assert type(msg) is list
                msg = cast(list[float | str | DAQ_RECEIVED_MESSAGE_TYPE], msg)
                unpacked_data = self._validate_and_extract_data(msg)
                if unpacked_data is None:
                    continue

                sensors = list(unpacked_data["data"].keys())
                if not wrote_header_flag:
                    writer.writerow(["Timestamp (ns) +- 10ns"] + sensors)
                    wrote_header_flag = True
                
                for i, timestamp in enumerate(unpacked_data["relative_timestamps_nanoseconds"]):
                    values = [unpacked_data["data"][sensor][i] for sensor in sensors]
                    writer.writerow([timestamp] + values)
            
        export_size = os.path.getsize(output_file_path)
        return "{:.2f} MB".format(export_size / (1024 * 1024))
