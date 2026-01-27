"""
The main module for the LabJack DAQ source.
"""

import sys
import threading
import time
from typing import NoReturn, TypedDict, cast

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


# Lock for print with lock.
printLock = threading.Lock()


# Print with lock.
# Ensuring that print statements are thread-safe
# for main and stream callback.
def printWithLock(string):
    global printLock
    with printLock:
        print(string)


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


# TODO: Implement all the other stuff needed for read callback (stream information class, etc.)
def ljm_stream_read_callback(arg):
    # TODO: Implement data reading and processing. Plus Omnibus send.
    # Consult:
    # - read_data of NI (also commented below)
    # - https://github.com/labjack/labjack-ljm-python/blob/master/Examples/More/Stream/stream_callback.py
    pass


# def read_data(ai: nidaqmx.Task) -> NoReturn:
#     # See config.py.example, config.RATE should be float
#     # Converting to nanoseconds to avoid floating point inaccuracy
#     READ_PERIOD: int = int(1 / cast(int, config.RATE) * 1000000000)

#     rates = []

#     # Relative timestamp starting point, starts at current time and scales by READ_PERIOD
#     # Use current time to have a unique starting point on every collection, ns to prevent floating point error
#     relative_last_read_time: float = time.time_ns()

#     now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())  # 2021-07-12_22-35-08
#     with open(f"log_{now}.dat", "wb") as log:
#         while True:
#             # use a list of 50 timestamps to keep track of the sample rate
#             rates.append(time.time())
#             if len(rates) > 50:
#                 rates.pop(0)

#             # read data config.READ_BULK at a time
#             # ai.read returns a single array if there is only one sensor and a nested array otherwise
#             data: list[float | int] | list[list[float | int]] = cast(
#                 list[float | int] | list[list[float | int]],
#                 ai.read(number_of_samples_per_channel=config.READ_BULK, timeout=5),
#             )
#             assert type(data) is list  # Ensure the above behaviour is enforced

#             # make sure the data is a nested list to ensure consistency
#             if data and not isinstance(data[0], list):
#                 data = cast(list[list[float | int]], [data])

#             # Ensure that list is either empty or nested
#             assert (not data) or (type(data[0]) is list)
#             data = cast(list[list[float | int]], data)

#             num_of_messages_read = 0 if not data else len(data[0])


#             relative_timestamps = list(
#                 range(
#                     relative_last_read_time,
#                     relative_last_read_time + READ_PERIOD * num_of_messages_read,
#                     READ_PERIOD,
#                 )
#             )

#             data_parsed: DAQ_SEND_MESSAGE_TYPE = {
#                 "timestamp": time.time(),
#                 "data": calibration.Sensor.parse(data),  # apply calibration
#                 "relative_timestamps_nanoseconds": relative_timestamps,
#                 "sample_rate": cast(int, config.RATE),
#                 "message_format_version": MESSAGE_FORMAT_VERSION,
#             }

#             # Calculate next staring timestamp
#             # Reset the timestamps to a new starting point if there were problems reading
#             relative_last_read_time = (
#                 time.time_ns()
#                 if not data or num_of_messages_read < config.READ_BULK
#                 else relative_timestamps[-1] + READ_PERIOD
#             )

#             # we can concatenate msgpack outputs as a backup logging option
#             log.write(msgpack.packb(data_parsed))

#             sender.send(CHANNEL, data_parsed)  # send data to omnibus

#             print(
#                 f"\rRate: {config.READ_BULK*len(rates)/(time.time() - rates[0]): >6.0f}  ",
#                 end="",
#             )


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
        numAddresses, aScanListNames = calibration.Sensor.setup(handle)
        aScanList = ljm.namesToAddresses(numAddresses, aScanListNames)[0]

        # Start LJM stream.
        ljm.eStreamStart(
            handle, config.SCANS_PER_READ, numAddresses, aScanList, config.SCAN_RATE
        )
        print(f"Number of addresses set up: {numAddresses}")
        print(f"Scan list names: {aScanListNames}")
        print(f"Stream started with a scan rate of {config.SCAN_RATE}Hz")

        try:
            ljm.setStreamCallback(handle, ljm_stream_read_callback)
            printWithLock("Stream running and callback set.")
        except KeyboardInterrupt:
            printWithLock("KeyboardInterrupt Triggered")
    except ljm.LJMError as e:
        print(f"Error handling LabJack device: {e}")
        sys.exit(1)

    # Stop LJM stream.
    print("Stopping stream...")
    ljm.eStreamStop(handle)
    ljm.close(handle)


if __name__ == "__main__":
    main()
