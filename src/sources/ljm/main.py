"""
The main module for the LabJack DAQ source.
"""

import signal
import sys
import threading
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


# Lock for print with lock.
printLock = threading.Lock()


# Print with lock.
# Ensuring that print statements are thread-safe
# for main and stream callback.
def printWithLock(string):
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


# Class to hold stream information.
class StreamInfo:
    def __init__(self):
        self.handle: int = 0
        self.scanRate: float = 0
        self.scansPerRead: int = 0
        self.streamLengthMS: int = 0
        self.done: bool = False
        self.numAddresses: int = 0
        self.aScanList = []
        self.aScanListNames = []
        self.aDataSize: int = 0
        self.aData: list[float] = []
        self.streamRead: int = 0
        self.totSkip: int = 0
        self.totScans: int = 0
        self.relative_last_read_time: int = 0


READ_PERIOD: int = int(1 / cast(int, config.SCAN_RATE) * 1000000000)
rates = []

# Relative timestamp starting point, starts at current time and scales by READ_PERIOD
# Use current time to have a unique starting point on every collection, ns to prevent floating point error


now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())  # 2021-07-12_22-35-08


# Function to pass to the callback function. This needs have one
# parameter/argument, which will be the handle.
def ljm_stream_read_callback(arg):
    if stream_info.handle != arg:
        print("myStreamReadCallback - Unexpected argument: %d" % (arg))
        return

    # Check if stream is done so that we don't output the print statement below.
    if stream_info.done:
        return

    rates.append(time.time())
    if len(rates) > 50:
        rates.pop(0)

    try:
        # Read from the stream.
        ret = ljm.eStreamRead(stream_info.handle)
        stream_info.aData = ret[0]
        _deviceScanBacklog = ret[1]
        _ljmScanBackLog = ret[2]

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
        for i in range(stream_info.numAddresses):
            data.append(
                [
                    stream_info.aData[j * stream_info.numAddresses + i]
                    for j in range(stream_info.scansPerRead)
                ]
            )

        num_of_messages_read = 0 if not data else len(data[0])

        relative_timestamps = list(
            range(
                stream_info.relative_last_read_time,
                stream_info.relative_last_read_time
                + READ_PERIOD * num_of_messages_read,
                READ_PERIOD,
            )
        )

        data_parsed: DAQ_SEND_MESSAGE_TYPE = {
            "timestamp": time.time(),
            "data": calibration.Sensor.parse(data),  # apply calibration
            "relative_timestamps_nanoseconds": relative_timestamps,
            "sample_rate": cast(int, stream_info.scanRate),
            "message_format_version": MESSAGE_FORMAT_VERSION,
        }

        # Calculate next staring timestamp.
        # Reset the timestamps to a new starting point if there were problems reading.
        stream_info.relative_last_read_time = (
            time.time_ns()
            if not data or num_of_messages_read < config.SCANS_PER_READ
            else relative_timestamps[-1] + READ_PERIOD
        )

        with open(f"log_{now}.dat", "ab") as log:
            log.write(msgpack.packb(data_parsed))

        # Send data to omnibus.
        sender.send(CHANNEL, data_parsed)

        print(
            f"\rRate: {config.SCANS_PER_READ * len(rates) / (time.time() - rates[0]): >6.0f}  ",
            end="",
        )

    # If LJM has called this callback, the data is valid, but LJM_eStreamRead
    # may return LJME_STREAM_NOT_RUNNING if another thread (such as the Python
    # main thread) has stopped stream.
    except ljm.LJMError as err:
        if err.errorCode == ljm.errorcodes.STREAM_NOT_RUNNING:
            printWithLock(
                "Error handling LJM Stream Read Callback: eStreamRead returned LJME_STREAM_NOT_RUNNING."
            )
        else:
            printWithLock(f"Error handling LJM Stream Read Callback: {err}")


# Create the global StreamInfo class which is used to pass information between
# the callback and main code.
stream_info = StreamInfo()


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

        # Stream Configuration
        stream_info.aScanListNames = aScanListNames
        stream_info.numAddresses = numAddresses
        stream_info.aScanList = aScanList
        stream_info.scanRate = config.SCAN_RATE
        stream_info.scansPerRead = config.SCANS_PER_READ
        stream_info.done = False
        stream_info.aDataSize = stream_info.numAddresses * stream_info.scansPerRead
        stream_info.handle = handle

        # Relative timestamp starting point, starts at current time and scales by READ_PERIOD.
        # Use current time to have a unique starting point on every collection, ns to prevent floating point error.
        stream_info.relative_last_read_time = time.time_ns()

        # Start LJM stream.
        stream_info.scanRate = ljm.eStreamStart(
            stream_info.handle,
            stream_info.scansPerRead,
            stream_info.numAddresses,
            stream_info.aScanList,
            stream_info.scanRate,
        )
        print(f"Number of addresses set up: {stream_info.numAddresses}")
        print(f"Scan list names: {stream_info.aScanListNames}")
        print(f"Stream started with a scan rate of {stream_info.scanRate} Hz")
        if stream_info.scanRate != config.SCAN_RATE:
            print(
                f"Warning: Configured scan rate ({config.SCAN_RATE} Hz) does not match actual scan rate ({stream_info.scanRate} Hz)."
            )

        try:
            ljm.setStreamCallback(stream_info.handle, ljm_stream_read_callback)
            printWithLock("Stream running and callback set.")
            # Make sure SIGINT is properly handled to stop the stream.
            # see: https://github.com/python/cpython/issues/80116
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            # Hang the main thread until an interrupt is triggered to stop the stream.
            printWithLock("Press Ctrl+C to stop...")
            threading.Event().wait()
        except KeyboardInterrupt:
            printWithLock("KeyboardInterrupt Triggered")

        # Stop LJM stream.
        print("Stopping stream...")
        stream_info.done = True
        ljm.eStreamStop(handle)
        ljm.close(handle)
    except ljm.LJMError as e:
        print(f"Error handling LabJack device: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
