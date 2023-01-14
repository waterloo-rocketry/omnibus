import time

i = 0

while True:
    print(f'{{"time": {i}}}', flush=True)
    i += 1
    time.sleep(1)
