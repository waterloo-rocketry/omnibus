import threading
import time
import sys

import msgpack
import nidaqmx

from omnibus import Sender, Message
import config
import calibration

calibration.Sensor.print()

system = nidaqmx.system.System.local()
if len(system.devices) == 0:
    print("Error: No device detected.")
    sys.exit(1)
if len(system.devices) > 1:
    print("Error: Multiple devices detected. Please only connect one device.")
    sys.exit(1)
print(f"Found device {system.devices[0].product_type}.")

sender = Sender("DAQ")

def read_data(ai):
    rates = []

    now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
    with open(f"log_{now}.dat", "wb") as log:
        while True:
            rates.append(time.time())
            if len(rates) > 50:
                rates.pop(0)
            data = ai.read(number_of_samples_per_channel=config.READ_BULK, timeout=5)

            data = {
                "timestamp": time.time(),
                "data": calibration.Sensor.parse(data)
            }

            log.write(msgpack.packb(data))

            sender.send(data)
            print(f"\rRate: {config.READ_BULK*len(rates)/(time.time() - rates[0]): >6.0f}  ", end='')


with nidaqmx.Task() as ai:
    calibration.Sensor.setup(ai)
    ai.timing.cfg_samp_clk_timing(config.RATE, sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS)

    ai.start()

    threading.Thread(target=read_data, args=(ai,), daemon=True).start()

    while True:
        time.sleep(1)
