import time
import sys

import nidaqmx
import zmq

SERVER_URL = "tcp://4.tcp.ngrok.io:15529"
SAMPLE_RATE = 10000 # Samples/sec.
READ_BULK = 200 # Read multiple samples at once for increased performance.

system = nidaqmx.system.System.local()
if len(system.devices) == 0:
    print("Error: No device detected.")
    sys.exit(1)
if len(system.devices) > 1:
    print("Error: Multiple devices detected. Please only connect one device.")
    sys.exit(1)

print(f"Found device {system.devices[0].product_type}.")

context = zmq.Context()
sender = context.socket(zmq.PUB)
sender.connect(SERVER_URL)

print("Connected to 0MQ server.")

with nidaqmx.Task() as task:
    # Set up an analog input voltage channel scaled to +-0.2 V on a differential input
    task.ai_channels.add_ai_voltage_chan("Dev1/ai16", min_val=-0.2, max_val=0.2, terminal_config=nidaqmx.constants.TerminalConfiguration.DIFFERENTIAL)

    # Set up a bunch of other analog channels on a single wire relative to ground, to saturate the data collection
    for c in [0, 1, 2, 3, 4, 5, 6, 7, 17, 18, 19, 20, 21, 22, 23]:
        task.ai_channels.add_ai_voltage_chan(f"Dev1/ai{c}", min_val=-10, max_val=10)

    # Continuous mode means don't quit after a certain number of samples.
    task.timing.cfg_samp_clk_timing(SAMPLE_RATE, sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS)

    print("Ready.")

    last = time.time()
    count = 0
    while True:
        data = task.read(number_of_samples_per_channel=READ_BULK)
        # "Calibration" (just ai16 for testing)
        data = (time.time(), [[(d - 0.000505) * 6550 for d in data[0]]] + data[1:])
        sender.send_pyobj(data) # Use pickle to seralize the data because I'm lazy
        count += READ_BULK

        if time.time() - last >= 0.2: # Update our output
            last = time.time()
            # task.in_stream.avail_samp_per_chan is the number of samples currently in each channel's buffer, which has size task.in_stream.input_buf_size
            print(f"\rSamples/sec: {count*5: >5}  Buffer health: {100 - task.in_stream.avail_samp_per_chan * 100 / task.in_stream.input_buf_size: >5.1f}%  ", end="")
            count = 0
