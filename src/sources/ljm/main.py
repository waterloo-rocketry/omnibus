"""
The main module for the LabJack DAQ source.
"""

import argparse
import sys
import time
from pathlib import Path
from typing import TypedDict, cast

import msgpack
import yaml

# Import the LabJack package
from labjack import ljm
from omnibus import Sender

import calibration

CONFIG_PATH = Path(__file__).parent / "config.yaml"

try:
    with open(CONFIG_PATH) as f:
        _cfg = yaml.safe_load(f)
except FileNotFoundError:
    print(
        "Error: config.yaml not found! Is config.yaml in the same folder as the ljm source?\n"
        "See 'config.yaml.example' for more info.",
        file=sys.stderr,
    )
    sys.exit(1)
except yaml.YAMLError as e:
    print(f"Error: Failed to parse config.yaml:\n{e}", file=sys.stderr)
    sys.exit(1)

try:
    _stream = _cfg["stream"]
    SCANS_PER_READ: int = int(_stream["scans_per_read"])
    SCAN_RATE: int = int(_stream["scan_rate"])
except (KeyError, TypeError, ValueError) as e:
    print(f"Error: Invalid stream configuration in config.yaml: {e}", file=sys.stderr)
    sys.exit(1)

_CONNECTION_MAP = {
    "single": calibration.Connection.SINGLE,
    "differential": calibration.Connection.DIFFERENTIAL,
}

try:
    for sensor_cfg in _cfg.get("sensors", []):
        cal_cfg = sensor_cfg["calibration"]
        cal_type = cal_cfg["type"]

        if cal_type == "linear":
            cal = calibration.LinearCalibration(
                slope=cal_cfg["slope"],
                offset=cal_cfg["offset"],
                unit=cal_cfg["unit"],
            )
        elif cal_type == "thermistor":
            cal = calibration.ThermistorCalibration(
                voltage=cal_cfg["voltage"],
                resistance=cal_cfg["resistance"],
                B=cal_cfg["B"],
                r_inf=cal_cfg["r_inf"],
            )
        else:
            print(
                f"Error: Unknown calibration type '{cal_type}' for sensor '{sensor_cfg.get('name', '?')}'.",
                file=sys.stderr,
            )
            sys.exit(1)

        connection_str = sensor_cfg["connection"].lower()
        if connection_str not in _CONNECTION_MAP:
            print(
                f"Error: Invalid connection '{connection_str}' for sensor '{sensor_cfg.get('name', '?')}'. "
                "Must be 'single' or 'differential'.",
                file=sys.stderr,
            )
            sys.exit(1)

        calibration.Sensor(
            name=sensor_cfg["name"],
            channel=sensor_cfg["channel"],
            input_range=sensor_cfg["input_range"],
            connection=_CONNECTION_MAP[connection_str],
            calibration=cal,
        )
except KeyError as e:
    print(f"Error: Missing required sensor field {e} in config.yaml.", file=sys.stderr)
    sys.exit(1)

calibration.Sensor.print()  # Print out all sensors and their AIN channels.

# Omnibus Channel Configuration
sender = Sender()
CHANNEL = "DAQ"
# Increment whenever data format change, so that new incompatible tools don't
# attempt to read old logs / messages.
MESSAGE_FORMAT_VERSION = 2  # Backwards compatible with original version.


class DAQ_SEND_MESSAGE_TYPE(TypedDict):
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
    There can be variation of +- 1ns for every point.
    Timestamps are based on initial time t_0 = time.time_ns(), meaning they should be always unique.
    Unit is nanoseconds.
    """
    # Example: [19, 22, 25] <- 1.3 and 2.3 from above was read at t0 = 19

    # Rate at which the messages were read, in Hz, dt = 1/sample_rate
    sample_rate: int

    # Arbitrary constant that validates that the received message format is compatible.
    # Increment MESSAGE_FORMAT_VERSION both here and in the Data Processing script whenever the structure changes.
    message_format_version: int


# Function to pass to the callback function. This needs have one
# parameter/argument, which will be the handle.
def read_data(handle, num_addresses, scans_per_read, scan_rate, *, quiet=False, no_built_in_log=False):
    # Converting to nanoseconds to avoid floating point inaccuracy.
    READ_PERIOD: int = int(1 / cast(int, scan_rate) * 1000000000)

    rates = []

    # Relative timestamp starting point, starts at current time and scales by READ_PERIOD.
    # Use current time to have a unique starting point on every collection, ns to prevent floating point error.
    relative_last_read_time: float = time.time_ns()

    log = None
    if not no_built_in_log:
        now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())  # 2021-07-12_22-35-08
        log = open(f"log_{now}.dat", "wb")

    try:
        while True:
            rates.append(time.time())
            if len(rates) > 50:
                rates.pop(0)

            # Read from the stream.
            sensor_values, _deviceScanBacklog, _ljmScanBackLog = ljm.eStreamRead(handle)

            # Convert sensor_values to DAQ data format.
            # sensor_values is a interleaved list of readings,
            # i.e. [chan0_scan0, chan1_scan0, ..., chanN_scan0,
            #   chan0_scan1, chan1_scan1, ..., chanN_scan1, ...,
            #   chan0_scanM, chan1_scanM, ..., chanN_scanM].
            # and we need to convert it to a nested list of
            # [[chan0_scan0, chan0_scan1, ..., chan0_scanM],
            #  [chan1_scan0, chan1_scan1, ..., chan1_scanM],
            #  ...
            #  [chanN_scan0, chanN_scan1, ..., chanN_scanM]]
            # Note that N = stream_info.numAddresses - 1,
            # and M = stream_info.scansPerRead - 1
            data: list[list[float | int]] = []
            for i in range(num_addresses):
                data.append(
                    [
                        sensor_values[j * num_addresses + i]
                        for j in range(scans_per_read)
                    ]
                )

            num_of_messages_read = 0 if not data else len(data[0])

            relative_timestamps = list(
                range(
                    relative_last_read_time,
                    relative_last_read_time + READ_PERIOD * num_of_messages_read,
                    READ_PERIOD,
                )
            )

            data_parsed: DAQ_SEND_MESSAGE_TYPE = {
                "timestamp": time.time(),
                "data": calibration.Sensor.parse(data),  # apply calibration
                "relative_timestamps_nanoseconds": relative_timestamps,
                "sample_rate": cast(int, scan_rate),
                "message_format_version": MESSAGE_FORMAT_VERSION,
            }

            # Calculate next staring timestamp.
            # Reset the timestamps to a new starting point if there were problems reading.
            relative_last_read_time = (
                time.time_ns()
                if not data or num_of_messages_read < scans_per_read
                else relative_timestamps[-1] + READ_PERIOD
            )

            if log:
                log.write(msgpack.packb(data_parsed))

            # Send data to omnibus.
            sender.send(CHANNEL, data_parsed)

            if not quiet:
                print(
                    f"\rRate: {scans_per_read * len(rates) / (time.time() - rates[0]): >6.0f}  ",
                    end="",
                )
    finally:
        if log:
            log.close()


def main():
    parser = argparse.ArgumentParser(description="LabJack DAQ Source")
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress continuous output except for errors and setup information",
    )
    parser.add_argument(
        "--no-built-in-log",
        action="store_true",
        help="Disable writing to the built-in log file",
    )
    args = parser.parse_args()

    try:
        # Open first found LabJack T7 device with any connection type and any indentifier.
        handle = ljm.openS("T7", "ANY", "ANY")

        info = ljm.getHandleInfo(handle)
        print(
            "Opened a LabJack with Device type: %i, Connection type: %i,\n"
            "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i"
            % (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5])
        )

        # Ensure triggered stream is disabled.
        ljm.eWriteName(handle, "STREAM_TRIGGER_INDEX", 0)
        # Enabling internally-clocked stream.
        ljm.eWriteName(handle, "STREAM_CLOCK_SOURCE", 0)

        # Setup sensors.
        num_addresses, a_scan_list_names = calibration.Sensor.setup(handle)
        a_scan_list = ljm.namesToAddresses(num_addresses, a_scan_list_names)[0]

        # Start LJM stream.
        scan_rate = ljm.eStreamStart(
            handle, SCANS_PER_READ, num_addresses, a_scan_list, SCAN_RATE
        )
        print(f"Number of addresses set up: {num_addresses}")
        print(f"Scan list names: {a_scan_list_names}")
        print(f"Stream started with a scan rate of {scan_rate} Hz")
        if scan_rate != SCAN_RATE:
            print(
                f"Warning: Configured scan rate ({SCAN_RATE} Hz) does not match actual scan rate ({scan_rate} Hz)."
            )

        try:
            read_data(
                handle, num_addresses, SCANS_PER_READ, scan_rate,
                quiet=args.quiet, no_built_in_log=args.no_built_in_log,
            )
        except KeyboardInterrupt:
            pass

        # Stop LJM stream.
        print("Stopping stream...")
        ljm.eStreamStop(handle)
        ljm.close(handle)
    except ljm.LJMError as e:
        print(f"Error handling LabJack device: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
