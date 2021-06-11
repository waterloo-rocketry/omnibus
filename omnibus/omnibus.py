from dataclasses import dataclass
import socket
import time

import msgpack
import zmq

from . import server


@dataclass(frozen=True)
class Message:
    """
    Represents a message as it is sent over the wire.
    """
    channel: str
    timestamp: float
    payload: 'typing.Any'


class OmnibusCommunicator:
    """
    Handles state shared between senders and receivers.
    """
    server_ip = None
    context = None

    def __init__(self):
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
            sock.settimeout(5)  # 5 second timeout
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
    Allows messages to be sent to all of the receivers listening on a channel.

    Although it is instantiated with a set channel it is actually possible
    to send messages on any channel by building the message yourself and passing
    it to send_message.
    """

    def __init__(self, channel: str):
        super().__init__()
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.connect(f"tcp://{self.server_ip}:{server.SOURCE_PORT}")
        self.channel = channel

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

    def send(self, payload):
        """
        Wrap a payload in a message object and send it on the sender's channel.
        """
        message = Message(self.channel, time.time(), payload)
        self.send_message(message)


class Receiver(OmnibusCommunicator):
    """
    Listens to a channel and receives all messages sent to it.

    Filtering is based on only the beginning of the channel name, so for example
    a receiver listening to the channel 'foo' will also receive messages sent
    to 'foobar', and a receiver listing to the channel '' will receive all
    messages.
    """

    def __init__(self, channel: str):
        super().__init__()
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect(f"tcp://{self.server_ip}:{server.SINK_PORT}")
        self.subscriber.setsockopt(zmq.SUBSCRIBE, channel.encode("utf-8"))

    def recv_message(self, timeout=None):
        """
        Receive one message from a sender.

        If timeout is None this blocks until a message is received. Otherwise it
        waits for timeout milliseconds to receive a message and returns None. A
        zero timeout is supported for nonblocking operation.
        """

        if self.subscriber.poll(timeout):
            channel, timestamp, payload = self.subscriber.recv_multipart()
            return Message(channel.decode("utf-8"), msgpack.unpackb(timestamp), msgpack.unpackb(payload, encoding = "utf-8"))
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
