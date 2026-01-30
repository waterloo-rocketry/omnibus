"""
The main module for the LabJack DAQ source.
"""

import sys
import time
from typing import TypedDict, cast

import msgpack

# Import the LabJack package
from labjack import ljm
from omnibus import Sender

import calibration

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
    config.setup()  # Initialize the sensors.
except KeyError as e:
    print(f"Error: {''.join(e.args)}.", file=sys.stderr)
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
def read_data(handle, num_addresses, scans_per_read, scan_rate):
    # Converting to nanoseconds to avoid floating point inaccuracy.
    READ_PERIOD: int = int(1 / cast(int, scan_rate) * 1000000000)

    rates = []

    # Relative timestamp starting point, starts at current time and scales by READ_PERIOD.
    # Use current time to have a unique starting point on every collection, ns to prevent floating point error.
    relative_last_read_time: float = time.time_ns()

    now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())  # 2021-07-12_22-35-08
    with open(f"log_{now}.dat", "wb") as log:
        while True:
            rates.append(time.time())
            if len(rates) > 50:
                rates.pop(0)

            # Read from the stream.
            read = ljm.eStreamRead(handle)
            aData = read[0]
            _deviceScanBacklog = read[1]
            _ljmScanBackLog = read[2]

            # Convert aData to DAQ data format.
            # aData is a interleaved list of readings,
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
                    [aData[j * num_addresses + i] for j in range(scans_per_read)]
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

            log.write(msgpack.packb(data_parsed))

            # Send data to omnibus.
            sender.send(CHANNEL, data_parsed)

            print(
                f"\rRate: {scans_per_read * len(rates) / (time.time() - rates[0]): >6.0f}  ",
                end="",
            )


def main():
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
            handle, config.SCANS_PER_READ, num_addresses, a_scan_list, config.SCAN_RATE
        )
        print(f"Number of addresses set up: {num_addresses}")
        print(f"Scan list names: {a_scan_list_names}")
        print(f"Stream started with a scan rate of {scan_rate} Hz")
        if scan_rate != config.SCAN_RATE:
            print(
                f"Warning: Configured scan rate ({config.SCAN_RATE} Hz) does not match actual scan rate ({scan_rate} Hz)."
            )

        try:
            read_data(handle, num_addresses, config.SCANS_PER_READ, scan_rate)
        except KeyboardInterrupt:
            print("KeyboardInterrupt Triggered")

        # Stop LJM stream.
        print("Stopping stream...")
        ljm.eStreamStop(handle)
        ljm.close(handle)
    except ljm.LJMError as e:
        print(f"Error handling LabJack device: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
