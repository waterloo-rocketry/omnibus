# Bit-banged SPI driver for NI DAQ boxes (which also does standard analog data collection)

# The driver uses the two analog outputs as sclk and mosi, since they support synchronization with analog inputs.
# It requires sclk to be looped back into an analog input for synchronization reasons, and also reads miso via another analog input.
# Lastly, it pulses SS high via a digital output on startup to keep the slave synced with the master.

# This driver can currently read analog data at ~20k samples/sec and interact with SPI at ~1100 bytes/sec (although with about 0.25 secs of latency between a write and its response).

import sys
import threading
import time

import numpy as np
import msgpack
import nidaqmx
from nidaqmx import stream_writers
import zmq

SERVER_URL = "tcp://192.168.0.2:5559"
RATE = 20000
READ_BULK = 200
TEST_SPI_BYTES = 40
SCLK = "ao0"
MOSI = "ao1"
SCLK_LOOPBACK = "ai0"
MISO = "ai8"
SS = "pfi4"
SPI_VOLTAGE = 5

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

aow_lock = threading.Lock()

# We control the analog outputs by writing to a buffer on the NI box which they then read from.
# However, we use it in a mode where it will not loop back to old data in the buffer if it runs dry, and so if it runs dry it crashes instead.
# This means that we need to keep the buffer saturated with zeroes. However, if we keep the buffer too full,
# there is unreasonable latency between when we "write" data and when it actually gets sent out / we can read in the result.
# This function constantly checks how full the buffer is and tries to keep it about 1/4 of a second full.
# This function runs alone in a thread so it can loop all it likes.
def saturate_zeros(ao, aow):
    t = time.time()
    while True:
        buf = ao.out_stream.curr_write_pos - ao.out_stream.total_samp_per_chan_generated # This is the number of samples currently in the buffer
        diff = RATE // 4 - buf # try to keep 0.25s in the buffer
        if diff > 0:
            with aow_lock:
                aow.write_many_sample(np.zeros((2, diff), dtype=np.float64))
        t += 0.25 / 2 # check at twice as fast as the amount we want in the buffer
        time.sleep(max(t - time.time(), 0))

# Here we read both the incoming SPI bits and general analog data.
# Note that because of how the synchronization works, our sclk loopback is actually one sample ahead of the corresponding miso value.
def read_spi(ai):
    last_miso = [0]
    bit = 7
    byte = 0
    bytes_in = []

    analog_avg = None
    spi_avg = None
    spi_time = time.time()
    while True:
        analog_time = time.time()
        sclk, miso, *data = ai.read(number_of_samples_per_channel=READ_BULK, timeout=0.1)
        miso, last_miso = last_miso + miso[:-1], miso[-1:] # account for the sclk loopback / miso offset
        for i in range(len(sclk)):
            if sclk[i] > SPI_VOLTAGE / 2: # Clock high, read a bit and add it to our WIP byte
                byte |= round(miso[i] / SPI_VOLTAGE) << bit
                if bit == 0:
                    bit = 7
                    bytes_in.append(byte)
                    byte = 0
                else:
                    bit -= 1

        # Sample analog data 'calibration'.
        data = (time.time(), "ANALOG", [[(d - 0.000505) * 6550 for d in data[0]]] + data[1:])
        sender.send(msgpack.packb(data))

        if len(bytes_in) > TEST_SPI_BYTES: # we've amassed a full SPI response
            if spi_avg is None:
                spi_avg = [time.time() - spi_time for _ in range(100)]
            else:
                spi_avg = spi_avg[1:] + [time.time() - spi_time]
            spi_data, bytes_in = bytes_in[:TEST_SPI_BYTES], bytes_in[TEST_SPI_BYTES:]
            sender.send(msgpack.packb((time.time(), "SPI", spi_data)))
            spi_time = time.time()

        if analog_avg is None:
            analog_avg = [time.time() - analog_time for _ in range(100)]
        else:
            analog_avg = analog_avg[1:] + [time.time() - analog_time]

        print(f"\rAnalog Rate: {READ_BULK/np.mean(analog_avg):.0f} samples/sec   SPI Rate: {TEST_SPI_BYTES/np.mean(spi_avg or [1]):.0f} bytes/sec   Buffer health: {100 - ai.in_stream.avail_samp_per_chan * 100 / max(ai.in_stream.input_buf_size, 1): >5.1f}%   ", end='')

# Encodes some bytes into the SPI pulses needed to write them, adds said pulses to the write queue.
def send(aow, bytes_out):
    clkdata = []
    mosidata = []
    for byte_out in bytes_out:
        # Since these are analog channels, a binary 1 is represented by a voltage.
        clkdata += [SPI_VOLTAGE*(n % 2) for n in range(16)] + [0]
        mosidata += [SPI_VOLTAGE*bool(byte_out & (1 << (n//2))) for n in range(15, -1, -1)] + [0] # keep data valid for a full clock pulse, 2 samples
    clkdata += [0]
    mosidata += [0]

    with aow_lock:
        aow.write_many_sample(np.array([clkdata, mosidata], dtype=np.float64))


with nidaqmx.Task() as ao, nidaqmx.Task() as ai, nidaqmx.Task() as do:
    # Set up our SPI channels
    ao.ao_channels.add_ao_voltage_chan(f"Dev1/{SCLK}")
    ao.ao_channels.add_ao_voltage_chan(f"Dev1/{MOSI}")
    ai.ai_channels.add_ai_voltage_chan(f"Dev1/{SCLK_LOOPBACK}", min_val=-10, max_val=10, terminal_config=nidaqmx.constants.TerminalConfiguration.RSE)
    ai.ai_channels.add_ai_voltage_chan(f"Dev1/{MISO}", min_val=-10, max_val=10, terminal_config=nidaqmx.constants.TerminalConfiguration.RSE)
    do.do_channels.add_do_chan(f"Dev1/{SS}")

    # Set up generic analog input channels
    ai.ai_channels.add_ai_voltage_chan("Dev1/ai16", min_val=-0.2, max_val=0.2, terminal_config=nidaqmx.constants.TerminalConfiguration.DIFFERENTIAL)

    for c in [1, 2, 3, 4, 5, 6, 7]:
        ai.ai_channels.add_ai_voltage_chan(f"Dev1/ai{c}", min_val=-10, max_val=10, terminal_config=nidaqmx.constants.TerminalConfiguration.RSE)

    ao.timing.cfg_samp_clk_timing(RATE, sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS)
    ai.timing.cfg_samp_clk_timing(RATE, source='/Dev1/ao/SampleClock', sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS) # synchronize our reading with when we write

    ao.out_stream.regen_mode = nidaqmx.constants.RegenerationMode.DONT_ALLOW_REGENERATION # disable repeating old data, instead error if we run out
    ao.out_stream.output_buf_size = RATE # one second of buffer. For latency, we want to keep this buffer as empty as possible.
    aow = stream_writers.AnalogMultiChannelWriter(ao.out_stream) # Lets us stream data into the buffer and thus out onto the pin.
    aow.auto_start = False
    aow.write_many_sample(np.zeros((2, RATE // 4), dtype=np.float64), timeout=0) # We need to write some data before we start the task, otherwise it complains

    do.write(True) # SS high to sync with the slave
    ao.start()

    threading.Thread(target=saturate_zeros, args=(ao, aow), daemon=True).start()

    time.sleep(0.1) # Give startup ripples a moment to settle before starting to read data
    do.write(False)
    ai.start()

    threading.Thread(target=read_spi, args=(ai,), daemon=True).start()

    inp = list(range(TEST_SPI_BYTES))
    while True:
        if ai.in_stream.avail_samp_per_chan / max(ai.in_stream.input_buf_size, 1)  < 0.2: # Monitor the input buffer to make sure we aren't writing data too fast.
            send(aow, inp)
