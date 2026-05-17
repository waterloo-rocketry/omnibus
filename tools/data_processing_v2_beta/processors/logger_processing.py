import csv
import json
from typing import Any, Iterable, Protocol


class FlattenableMessage(Protocol):
    def to_flat_dict(self) -> dict[str, Any]:
        ...


class LoggerDataProcessor:
    """
    Converts parsed telemetry messages into CSV or JSON.
    Expects each parsed entry to be:
        (source: str, logger_time: float, message: FlattenableMessage)
    """

    MASTER_COLUMNS = [
        # Metadata
        "time",
        "logger_time",
        "msg_prio",
        "board_type_id",
        "board_inst_id",
        "msg_type",
        "msg_metadata",

        # Primary Data
        "pressure",
        "temp",
        "imu_id",
        "linear_accel",
        "angular_velocity",
        "mag",

        # GPS Data
        "hrs",
        "mins",
        "secs",
        "dsecs",
        "degs",
        "dmins",
        "direction",
        "altitude",
        "daltitude",
        "unit",
        "num_sats",
        "quality",

        # Actuators & Power
        "actuator",
        "curr_state",
        "req_state",
        "sensor_id",
        "value",

        # System Health & Errors
        "general_error_bitfield",
        "board_error_bitfield",
        "error",
    ]

    def __init__(self) -> None:
        self.column_to_idx = {
            name: i for i, name in enumerate(self.MASTER_COLUMNS)
        }

    def _serialize_value(self, value: Any) -> Any:
        """Make values CSV-safe."""
        if isinstance(value, (list, dict)):
            return json.dumps(value)
        return value

    def _flatten_message(
        self,
        parsed_entry: tuple[str, float, FlattenableMessage],
    ) -> dict[str, Any]:

        if len(parsed_entry) != 3:
            raise ValueError(f"Expected 3-item tuple, got {len(parsed_entry)}")

        _, logger_time, message = parsed_entry

        flat = message.to_flat_dict()

        # enforce logger_time consistency
        flat["logger_time"] = logger_time

        return flat

    def _map_to_csv_row(
        self,
        parsed_entry: tuple[str, float, FlattenableMessage],
    ) -> list[Any]:

        flat = self._flatten_message(parsed_entry)

        row = [""] * len(self.MASTER_COLUMNS)

        for key, value in flat.items():
            idx = self.column_to_idx.get(key)
            if idx is None:
                continue
            row[idx] = self._serialize_value(value)

        return row

    def process_log_and_write_csv(
        self,
        output_file: str,
        parsed_messages: Iterable[tuple[str, float, FlattenableMessage]],
    ) -> None:

        with open(output_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(self.MASTER_COLUMNS)

            for msg in parsed_messages:
                writer.writerow(self._map_to_csv_row(msg))

    def process_log_and_write_json(
        self,
        output_file: str,
        parsed_messages: Iterable[tuple[str, float, FlattenableMessage]],
    ) -> None:

        json_data = [
            self._flatten_message(msg)
            for msg in parsed_messages
        ]

        with open(output_file, "w") as f:
            json.dump(json_data, f, indent=4)