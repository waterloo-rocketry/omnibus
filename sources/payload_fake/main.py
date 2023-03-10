from omnibus import Sender
import random
import time
import math

SAMPLE_RATE = 10  # total samples/second

running_angles = [0, 0, 0]
count = 0


sender = Sender()
CHANNEL = "StateEstimation"


def shift_angle(angle):
    angle[0] = (angle[0] + math.pi + 0.01) % (2 * math.pi) - math.pi
    angle[1] = (angle[1] + math.pi + 0.01) % (2 * math.pi) - math.pi
    angle[2] = (angle[2] + math.pi + 0.01) % (2 * math.pi) - math.pi
    return angle


dots = 0
counter = 0
while True:
    start = time.time()
    # send a tuple of when the data was recorded and an array of the data for each channel
    running_angles = shift_angle(running_angles)
    data = {
        "timestamp": start,
        "data": {
            "orientation": running_angles,
            "position": [10 * math.cos(count/100), 10 * math.sin(count/100), 2 * math.sin(count/10)]
        }
    }

    count += 1

    # Cool continuously updating print statment
    print("\rSending", end="")
    if counter % (20*5) == 0:
        print("   ", end="")
    elif counter % 20 == 0:
        for i in range(dots):
            print(".", end="")
        if dots == 3:
            dots = 0
        else:
            dots += 1

    counter += 1

    sender.send(CHANNEL, data)
    time.sleep(1 / SAMPLE_RATE)
