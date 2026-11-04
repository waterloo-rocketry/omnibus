"""
The main module for the LabJack DAQ source.
"""

import argparse
import sys
import signal
import time
from typing import TypedDict

import msgpack

# Import the LabJack package
from labjack import ljm  # pyright: ignore[reportMissingTypeStubs]
from omnibus import Sender

import calibration

if sys.platform == "win32":
    import win_precise_time  # pyright: ignore[reportMissingImports]

    def get_host_time() -> float:
        return float(win_precise_time.time())  # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]

else:
    def get_host_time() -> float:
        return float(time.time())

try:
    import config  # pyright: ignore[reportMissingImports]
except ImportError as e:
    print(
        """Error: Importing config failed! Is config.py in the same folder as ljm source?
See 'config.py.example' for more info.\n"""
        + str(e.msg),
        file=sys.stderr,
    )
    sys.exit(1)


try:
    config.setup()  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]  # Initialize the sensors.
except KeyError as e:
    print(f"Error: {''.join(e.args)}.", file=sys.stderr)
    sys.exit(1)

calibration.Sensor.print()  # Print out all sensors and their AIN channels.

# Omnibus Channel Configuration
CHANNEL = "DAQ/ljm"
# Increment whenever data format change, so that new incompatible tools don't
# attempt to read old logs / messages.
MESSAGE_FORMAT_VERSION = 3  # Backwards compatible with original version.


class DAQ_SEND_MESSAGE_TYPE(TypedDict):
    timestamp: float
    data: dict[str, list[float]]
    """
    Each sensor groups a certain number of readings, the bulk read rate of the DAQ.
    The length of that list corresponds to the length of relative_timestamps below.
    The floating point numbers are arbitrary values depending on the unit of the sensor configured when it was recorded.
    """
    # Example: {
    #     "NPT-201: Nitrogen Fill PT (psi)": [1.3, 2.3, 4.3],
    #     "OPT-201: Ox Fill PT (psi)": [2.3, 4.5, 7.2],
    #     ...
    # }
    # 1.3 and 2.3 are the readings for each sensor at t0, 2.3 and 4.5 for t1, etc.

    relative_timestamps: list[float]
    """
    Corresponding timestamps for each reading of every sensors, calculated from the actual
    scan rate (dt = 1 / scan_rate) from a host start time.
    Unit is seconds.
    """
    # Example: [19, 22, 25] <- 1.3 and 2.3 from above was read at t0 = 19

    # Configured rate at which the messages were read, in Hz.
    sample_rate: int

    # Arbitrary constant that validates that the received message format is compatible.
    # Increment MESSAGE_FORMAT_VERSION both here and in the Data Processing script whenever the structure changes.
    message_format_version: int


# Function to pass to the callback function. This needs have one
# parameter/argument, which will be the handle.
def read_data(handle: int, num_addresses: int, scans_per_read: int, scan_rate: float, sender: Sender, *, quiet: bool = False, no_built_in_log: bool = False) -> None:
    configured_sample_rate = int(config.SCAN_RATE)  # pyright: ignore[reportAttributeAccessIssue, reportUnknownArgumentType, reportUnknownMemberType]
    if configured_sample_rate <= 0:
        raise ValueError("config.SCAN_RATE must cast to a positive integer")

    if scan_rate <= 0:
        raise ValueError("scan_rate must be positive")

    read_period_seconds: float = 1 / scan_rate

    # Starting point for deriving timestamps from the cumulative sample count.
    initial_host_start_time = get_host_time()
    total_samples_read = 0

    log = None
    if not no_built_in_log:
        now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())  # 2021-07-12_22-35-08
        log = open(f"log_{now}.dat", "wb")

    rates: list[float] = []
    try:
        while True:
            rates.append(time.time())
            if len(rates) > 50:
                rates.pop(0)

            # Read from the stream.
            from typing import cast
            result = cast(tuple[list[float | int], float, float], ljm.eStreamRead(handle))  # pyright: ignore[reportUnknownMemberType]
            sensor_values = result[0] if result else []  # pyright: ignore[reportUnknownVariableType]

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
                row: list[float | int] = []
                for j in range(scans_per_read):
                    row.append(sensor_values[j * num_addresses + i])
                data.append(row)

            num_of_messages_read = 0 if not data else len(data[0])

            relative_timestamps: list[float] = [
                initial_host_start_time
                + (total_samples_read + sample_index) * read_period_seconds
                for sample_index in range(num_of_messages_read)
            ]

            data_parsed: DAQ_SEND_MESSAGE_TYPE = {
                "timestamp": get_host_time(),
                "data": calibration.Sensor.parse(data),  # apply calibration
                "relative_timestamps": relative_timestamps,
                "sample_rate": configured_sample_rate,
                "message_format_version": MESSAGE_FORMAT_VERSION,
            }

            # Reset the timestamp baseline if there were problems reading.
            if not data or num_of_messages_read < scans_per_read:
                initial_host_start_time = get_host_time()
                total_samples_read = 0
            else:
                total_samples_read += num_of_messages_read

            if log:
                log.write(msgpack.packb(data_parsed))

            # Send data to omnibus.
            sender.send(CHANNEL, data_parsed)  # pyright: ignore[reportUnknownMemberType]

            if not quiet:
                if rates:
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
    parser.add_argument(
        "--omnibus-server-host",
        default=None,
        help="Omnibus server host/IP to connect to. If omitted, auto-discovery is used.",
    )
    args = parser.parse_args()

    # Omnibus sender, connecting to the server address passed via CLI (or
    # auto-discovered when not provided).
    sender = Sender(server_ip=args.omnibus_server_host)

    handle: int | None = None # LJM Handle
    try:
        # Open first found LabJack T7 device with any connection type and any indentifier.
        handle = ljm.openS("T7", "ANY", "ANY")

        info = ljm.getHandleInfo(handle)  # pyright: ignore[reportUnknownMemberType]
        print(
            "Opened a LabJack with Device type: %i, Connection type: %i,\n"
            "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i"
            % (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5])  # pyright: ignore[reportUnknownMemberType]
        )

        # Ensure triggered stream is disabled.
        ljm.eWriteName(handle, "STREAM_TRIGGER_INDEX", 0)  # pyright: ignore[reportUnknownMemberType]
        # Enabling internally-clocked stream.
        ljm.eWriteName(handle, "STREAM_CLOCK_SOURCE", 0)  # pyright: ignore[reportUnknownMemberType]

        # Setup sensors.
        num_addresses, a_scan_list_names = calibration.Sensor.setup(handle)  # pyright: ignore[reportArgumentType, reportGeneralTypeIssues, reportUnknownVariableType]
        a_scan_list = ljm.namesToAddresses(num_addresses, a_scan_list_names)[0]  # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType, reportUnknownVariableType]

        # Start LJM stream.
        scan_rate = ljm.eStreamStart(  # pyright: ignore[reportUnknownMemberType]
            handle, config.SCANS_PER_READ, num_addresses, a_scan_list, config.SCAN_RATE  # pyright: ignore[reportAttributeAccessIssue, reportUnknownArgumentType, reportUnknownMemberType]
        )
        print(f"Number of addresses set up: {num_addresses}")
        print(f"Scan list names: {a_scan_list_names}")
        print(f"Stream started with a scan rate of {scan_rate} Hz")
        if scan_rate != config.SCAN_RATE:  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
            print(
                f"Warning: Configured scan rate ({config.SCAN_RATE} Hz) does not match actual scan rate ({scan_rate} Hz)."  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
            )
        read_data(
            handle, num_addresses, config.SCANS_PER_READ, scan_rate, sender,  # pyright: ignore[reportAttributeAccessIssue, reportUnknownArgumentType, reportUnknownMemberType]
            quiet=args.quiet, no_built_in_log=args.no_built_in_log,
        )
    except ljm.LJMError as e:
        print(f"Error handling LabJack device: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        try:
            ljm.eStreamStop(handle)  # pyright: ignore[reportUnknownMemberType]
        except Exception as e:
            pass
        try:
            ljm.close(handle)  # pyright: ignore[reportUnknownMemberType]
        except Exception as e:
            pass

if __name__ == "__main__":
    def handle_exit(*_args: object) -> None:
        sys.exit(0)
    signal.signal(signal.SIGTERM, handle_exit)
    signal.signal(signal.SIGINT, handle_exit)
    main()
