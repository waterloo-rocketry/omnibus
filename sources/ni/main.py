import time
import sys
import msgpack
import nidaqmx

from omnibus import Sender
import calibration
import numpy as np

from typing import cast, Any

try:
    import config  # pyright: ignore[reportMissingImports]
except ImportError as e:
    print(
        f"""Error: Importing config failed! Is config.py in the same folder as NI Source? 
See 'config.py.example' for more info.\n"""
        + str(e.msg),
        file=sys.stderr,
    )
    sys.exit(1)


try:
    config.setup()  # initialize the sensors
except KeyError as e:
    print(f"Error: {''.join(e.args)}.", file=sys.stderr)
    sys.exit(1)

calibration.Sensor.print()  # print out sensors and their ai channels

system = nidaqmx.system.System.local()  # pyright: ignore[reportAttributeAccessIssue]
if len(system.devices) == 0:
    print("Error: No device detected.")
    sys.exit(1)
if len(system.devices) > 1:
    print("Error: Multiple devices detected. Please only connect one device.")
    sys.exit(1)
print(f"Found device {system.devices[0].product_type}.")

sender = Sender()  # omnibus channel
CHANNEL = "DAQ"
# Increment whenever data format change, so that new incompatible tools don't
# attempt to read old logs / messages
MESSAGE_FORMAT_VERSION = 2  # Backwards compatible with original


def read_data(ai: nidaqmx.Task):
    # See config.example.py, config.RATE should be float
    # Converting to nanoseconds to avoid floating point inaccuracy
    READ_PERIOD: int = int(1 / cast(int, config.RATE) * 1000000000)

    rates = []
    # Relative timestamp starting point, starts at current time and scales by READ_PERIOD
    # Use current time to reduce risk of interruptions in data collection
    relative_last_read_time: float = time.time_ns()
    now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())  # 2021-07-12_22-35-08
    with open(f"log_{now}.dat", "wb") as log:
        while True:
            # use a list of 50 timestamps to keep track of the sample rate
            rates.append(time.time())
            if len(rates) > 50:
                rates.pop(0)

            # read data config.READ_BULK at a time
            # ai.read returns a single array if there is only one sensor and a nested array otherwise
            data = cast(
                list[Any] | list[list[Any]],
                ai.read(number_of_samples_per_channel=config.READ_BULK, timeout=5),
            )
            assert type(data) is list  # Ensure the above behaviour is enforced

            # make sure the data is a nested list to ensure consistency
            if data and not isinstance(data[0], list):
                data = cast(list[list[Any]], [data])

            # Ensure that list is either empty or nested
            assert (not data) or (type(data[0]) is list)

            num_of_messages_read = 0 if not data else len(data[0])

            relative_timestamps = np.arange(
                relative_last_read_time,
                relative_last_read_time + READ_PERIOD * num_of_messages_read,
                READ_PERIOD,
            ).tolist()

            data_parsed = {
                "timestamp": time.time(),
                "data": calibration.Sensor.parse(data),  # apply calibration
                "relative_timestamps_nanoseconds": relative_timestamps,
                "sample_rate": config.RATE,
                "message_format_version": MESSAGE_FORMAT_VERSION,
            }

            # Calculate next staring timestamp
            relative_last_read_time = (
                time.time_ns() if not data else relative_timestamps[-1] + READ_PERIOD
            )

            # we can concatenate msgpack outputs as a backup logging option
            log.write(cast(bytes, msgpack.packb(data_parsed)))

            sender.send(CHANNEL, data_parsed)  # send data to omnibus

            print(
                f"\rRate: {config.READ_BULK*len(rates)/(time.time() - rates[0]): >6.0f}  ",
                end="",
            )


with nidaqmx.Task() as ai:
    calibration.Sensor.setup(ai)

    # continuously sample at config.RATE samps/sec
    ai.timing.cfg_samp_clk_timing(
        rate=config.RATE,
        sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,  # pyright: ignore[reportAttributeAccessIssue]
    )
    ai.start()

    read_data(ai)
