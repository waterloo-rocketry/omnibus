# pyright: strict

from dataclasses import dataclass
from typing import Generic, TypedDict, TypeVar

MESSAGE_FORMAT_VERSION = 2
MESSAGE_FORMAT_VERSION_V3 = 3


class DAQReceivedMessageV2(TypedDict):
    timestamp: float
    data: dict[str, list[float]]
    relative_timestamps_nanoseconds: list[int]
    sample_rate: int
    message_format_version: int


class DAQReceivedMessageV3(TypedDict):
    timestamp: float
    data: dict[str, list[float]]
    relative_timestamps: list[int | float]
    sample_rate: int
    message_format_version: int


PayloadT = TypeVar("PayloadT", DAQReceivedMessageV2, DAQReceivedMessageV3)


@dataclass(frozen=True)
class DAQFormatConfig(Generic[PayloadT]):
    message_format_version: int
    timestamp_field: str
    timestamp_header: str
    expected_data_shape: dict[str, type[object]]


V2_FORMAT = DAQFormatConfig[DAQReceivedMessageV2](
    message_format_version=MESSAGE_FORMAT_VERSION,
    timestamp_field="relative_timestamps_nanoseconds",
    timestamp_header="Timestamp (ns) +- 10ns",
    expected_data_shape={
        "timestamp": float,
        "data": dict,
        "relative_timestamps_nanoseconds": list,
        "sample_rate": int,
        "message_format_version": int,
    },
)

V3_FORMAT = DAQFormatConfig[DAQReceivedMessageV3](
    message_format_version=MESSAGE_FORMAT_VERSION_V3,
    timestamp_field="relative_timestamps",
    timestamp_header="Timestamp (s)",
    expected_data_shape={
        "timestamp": float,
        "data": dict,
        "relative_timestamps": list,
        "sample_rate": int,
        "message_format_version": int,
    },
)

