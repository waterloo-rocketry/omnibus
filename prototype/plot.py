import collections
import time

import matplotlib.pyplot as plt
import matplotlib.animation as anim
import numpy as np
import zmq

context = zmq.Context()

receiver = context.socket(zmq.SUB)
receiver.connect("tcp://localhost:5560") # or whatever url the server is running on
receiver.setsockopt(zmq.SUBSCRIBE, b"") # subscribe to all messages

print("Connected to 0MQ server.")

# Set up 8x2 grid of plots
fig = plt.figure()
axes = []
for i in range(16):
    ax = fig.add_subplot(8, 2, i+1)
    ax.set_ylim(-10, 10)
    ax.grid(which='both')
    axes.append(ax)

# 16 channels each with 600 data points (6 seconds)
data = [collections.deque(np.zeros(6*100)) for _ in range(16)]
lines = [ax.plot(channel, animated=True, alpha=0.5)[0] for channel, ax in zip(data, axes)]

# Make the plots large enough to be usuable
fig.tight_layout()
plt.subplots_adjust(wspace=0.1, hspace=0.1)

last = time.time()
count = 0
fps = 0
def update(_):
    global last, count, fps # yes, yes, I know

    sent = time.time() + 1
    # Since our bottleneck is matplotlib, get all the data we can and graph it all at once
    while receiver.poll(1): # Timeout of 1 ms checking for new data
        sent, new = receiver.recv_pyobj() # pickle compression because I'm lazy

        for channel, points, line in zip(data, new, lines):
            # Just plot the first data point. Since the server bulk reads 10 samples at
            # once this effectively downsamples to 100 samples/sec
            channel.popleft()
            channel.append(points[0])
            line.set_ydata(channel)
        count += len(new[0])

    fps += 1

    if time.time() - last > 0.2:
        last = time.time()
        print(f"\rSamples/second: {count*5}  FPS: {fps*5}  Lag: {time.time() - sent:.2f}   ", end='')
        count = 0
        fps = 0

    # Return the objects we changed to FuncAnim
    return lines

# Try to animate at 30fps. Set interval to 0 for unlimited.
# We need to keep this variable around because of garbage collection magic.
a = anim.FuncAnimation(fig, update, interval=1000/30, blit=True)
plt.show()
