import socket
import threading
import time
from typing import NoReturn

import zmq
from zmq.devices import ThreadProxy

try:
    from .util import BuildInfoManager
except ImportError:
    from util import BuildInfoManager  # pyright: ignore[reportImplicitRelativeImport]

SOURCE_PORT = 5075
SINK_PORT = 5076
BROADCAST_PORT = 5077


def get_ip():
    """
    Return our best guess for this machine's IP on the LAN.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't need to be reachable
        s.connect(("255.255.255.255", 1))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def ip_broadcast() -> NoReturn:
    """
    Periodically send a UDP broadcast to the LAN. Sources and sinks can listen
    to who sent the broadcast (filtering based on the content) to find our ip.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:  # UDP socket
        # Allow the address to be re-used for when running multiple components
        # on the same machine
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # broadcast to LAN
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # This runs in a separate thread so we can loop
        while True:
            # 255.255.255.255 is a magic IP that means 'broadcast to the LAN'
            sock.sendto(b"omnibus", ("255.255.255.255", BROADCAST_PORT))
            time.sleep(0.5)


def server() -> NoReturn:
    """
    Run the Omnibus server, display the current messages/sec.
    """
    # Initialize BuildInfoManager to print build info
    bim = BuildInfoManager("Omnibus Server")
    bim.print_startup_screen()
    bim.print_app_name()

    context = zmq.Context()
    # Proxy messages in a separate thread
    proxy = ThreadProxy(zmq.SUB, zmq.PUB, zmq.PUB)
    proxy.bind_in(f"tcp://*:{SOURCE_PORT}")
    proxy.setsockopt_in(zmq.SUBSCRIBE, b"")
    proxy.bind_out(f"tcp://*:{SINK_PORT}")
    # Use in-process communication for the monitor socket
    proxy.bind_mon("inproc://mon")
    proxy.daemon = True
    proxy.context_factory = lambda: context

    proxy.start()
    # periodically broadcast our IP
    threading.Thread(target=ip_broadcast, daemon=True).start()

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


if __name__ == "__main__":
    try:
        server()
    except KeyboardInterrupt:
        pass
