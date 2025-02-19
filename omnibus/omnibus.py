from dataclasses import dataclass
import socket
import time
import typing

import msgpack
import zmq
from datetime import datetime
from .pretty_startup import run_startup_screen

try:
    from . import server
except ImportError:
    # Python complains if we run `python -m omnibus` from the omnibus folder.
    # This works around that complaint.
    import server

# Python also doesn't execute __main__ if we're in the omnibus folder.
# If that is the case (we were directly executed), start the server ourselves.
if __name__ == "__main__":
    server.server()


@dataclass(frozen=True)
class Message:
    """
    Represents a message as it is sent over the wire.
    """
    channel: str
    timestamp: float
    payload: typing.Any


class OmnibusCommunicator:
    """
    Handles state shared between senders and receivers.
    """
    server_ip = None
    context = None
    def __init__(self):
        run_startup_screen()
        if self.context is None:
            OmnibusCommunicator.context = zmq.Context()
        if self.server_ip is None:
            OmnibusCommunicator.server_ip = self._recv_ip()

    def _recv_ip(self):
        """
        Listen for a UDP broadcast from the server telling us its IP. If the
        broadcast isn't received, prompt to manually enter the IP.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:  # UDP
            # Allow the address to be re-used for when running multiple
            # components on the same machine
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(0.6)  # 0.6 second timeout
            sock.bind(('', server.BROADCAST_PORT))  # listen for broadcasts
            print("Listening for server IP...")
            while True:
                try:
                    data, (addr, _) = sock.recvfrom(16)
                    if data == b'omnibus':
                        print(f"Found {addr}")
                        return addr
                except socket.timeout:
                    pass
                print("Could not detect server IP. Please ensure it is running.")
                if ip := input("Press enter to retry or manually enter the server IP: ").strip():
                    return ip
                print("Retrying...")


class Sender(OmnibusCommunicator):
    """
    Allows messages to be sent to all of the receivers listening on the provided
    channel.
    """

    def __init__(self):
        super().__init__()
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.connect(f"tcp://{self.server_ip}:{server.SOURCE_PORT}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] Omnibus sending to {self.server_ip}")

    def send_message(self, message: Message):
        """
        Send a built message object to all receivers.

        Note that channel used is specified by the message object rather than
        the sender.
        """
        self.publisher.send_multipart([
            message.channel.encode("utf-8"),
            msgpack.packb(message.timestamp),
            msgpack.packb(message.payload)
        ])

    def send(self, channel: str, payload):
        """
        Wrap a payload in a message object and send it on a provided channel.
        """
        message = Message(channel, time.time(), payload)
        self.send_message(message)


class Receiver(OmnibusCommunicator):
    """
    Listens to a number of channels and receives all messages sent to them.

    Filtering is based on only the beginning of the channel name, so for example
    a receiver listening to the channel 'foo' will also receive messages sent
    to 'foobar', and a receiver listing to the channel '' will receive all
    messages.
    """
    ## PRIVATE PROPERTIES ##
    __channels = []
    # Keep track of last received message, only second granularity is needed
    # so time.time() is good enough on any platform
    __last_online_check = time.time()
    __disconnected = True
    ## END PRIVATE PROPERTIES ##

    def __init__(self, *channels):
        super().__init__()
        self.__channels = channels
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect(f"tcp://{self.server_ip}:{server.SINK_PORT}")
        for channel in channels:
            self.subscriber.setsockopt(zmq.SUBSCRIBE, channel.encode("utf-8"))
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] Omnibus receiving from {self.server_ip}")
        

    def recv_message(self, timeout=None):
        """
        Receive one message from a sender.

        If timeout is None this blocks until a message is received. Otherwise it
        waits for timeout milliseconds to receive a message and returns None. A
        zero timeout is supported for nonblocking operation.
        """

        if self.subscriber.poll(timeout):
            if self.__disconnected:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] Omnibus Receiver is online!")
            self.__disconnected = False
            channel, timestamp, payload = self.subscriber.recv_multipart()
            self.__last_online_check = time.time()
            return Message(channel.decode("utf-8"), msgpack.unpackb(timestamp), msgpack.unpackb(payload))
        if time.time() - self.__last_online_check >= 5:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [WARN] No messages received for a while, is Omnibus online?")
            self.__disconnected = True
            self.reset()
            self.__last_online_check = time.time()
        return None


    def recv(self, timeout=None):
        """
        Receive the payload of one message from a sender, discarding metadata.

        If timeout is None this blocks until a message is received. Otherwise it
        waits for timeout milliseconds to receive a message and returns None. A
        zero timeout is supported for nonblocking operation.
        """

        if message := self.recv_message(timeout):
            return message.payload
        return None
    

    def reset(self):
        self.subscriber.close(0)
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect(f"tcp://{self.server_ip}:{server.SINK_PORT}")
        for channel in self.__channels:
            self.subscriber.setsockopt(zmq.SUBSCRIBE, channel.encode("utf-8"))
        
