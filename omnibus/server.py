import socket
import time

import zmq
from zmq.devices import ThreadProxy

SOURCE_PORT = 5075
SINK_PORT = 5076


def get_ip():
    """
    Return our best guess for this machine's IP on the LAN.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't need to be reachable
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def server():
    """
    Run the Omnibus server, display the current messages/sec.
    """
    context = zmq.Context()

    proxy = ThreadProxy(zmq.SUB, zmq.PUB, zmq.PUB)  # proxies messages in a separate thread
    proxy.bind_in(f"tcp://*:{SOURCE_PORT}")
    proxy.setsockopt_in(zmq.SUBSCRIBE, b"")
    proxy.bind_out(f"tcp://*:{SINK_PORT}")
    proxy.bind_mon("inproc://mon")  # use in-process communication for the monitor socket
    proxy.daemon = True
    proxy.context_factory = lambda: context

    proxy.start()

    local_ip = get_ip()
    print(f"Serving {local_ip}:{SOURCE_PORT} -> {local_ip}:{SINK_PORT}")

    # The monitor receives all proxied messages. With normal proxies this means
    # messages going in both directions, but since this is a pub/sub proxy it
    # just receives the same messages as any other sink.
    monitor = context.socket(zmq.SUB)
    monitor.connect("inproc://mon")
    monitor.setsockopt(zmq.SUBSCRIBE, b"")

    t = time.time()
    count = 0
    while True:
        if monitor.poll(200):  # 200ms timeout
            monitor.recv_multipart()
            count += 1
        if time.time() - t > 0.2:
            print(f"\r{count*5: <5} msgs/sec", end="")
            t = time.time()
            count = 0


if __name__ == '__main__':
    server()
