import time
import sys

import msgpack
import nidaqmx

from omnibus import Sender
import config
import calibration

try:
    config.setup()  # initialize the sensors
except KeyError as e:
    print(f"Error: {''.join(e.args)}.")
    sys.exit(1)

calibration.Sensor.print()  # print out sensors and their ai channels

system = nidaqmx.system.System.local()
if len(system.devices) == 0:
    print("Error: No device detected.")
    sys.exit(1)
if len(system.devices) > 1:
    print("Error: Multiple devices detected. Please only connect one device.")
    sys.exit(1)
print(f"Found device {system.devices[0].product_type}.")

sender = Sender()  # omnibus channel
CHANNEL = "DAQ"


def read_data(ai):
    rates = []

    now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())  # 2021-07-12_22-35-08
    with open(f"log_{now}.dat", "wb") as log:
        while True:
            # use a list of 50 timestamps to keep track of the sample rate
            rates.append(time.time())
            if len(rates) > 50:
                rates.pop(0)

            # read data config.READ_BULK at a time
            # ai.read returns a single array if there is only one sensor and a nested array otherwise
            data = ai.read(number_of_samples_per_channel=config.READ_BULK, timeout=5)
            # make sure the data is a nested list to ensure consistency
            if data != [] and not isinstance(data[0], list):
                data = [data]

            data = {
                "timestamp": time.time(),
                "data": calibration.Sensor.parse(data)  # apply calibration
            }

            # we can concatenate msgpack outputs as a backup logging option
            log.write(msgpack.packb(data))

            sender.send(CHANNEL, data)  # send data to omnibus

            print(
                f"\rRate: {config.READ_BULK*len(rates)/(time.time() - rates[0]): >6.0f}  ", end='')


with nidaqmx.Task() as ai:
    calibration.Sensor.setup(ai)

    # continuously sample at config.RATE samps/sec
    ai.timing.cfg_samp_clk_timing(
        config.RATE, sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS)
    ai.start()

    read_data(ai)
