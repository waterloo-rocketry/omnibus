from dataclasses import dataclass
import time

import msgpack
import zmq

context = zmq.Context()


@dataclass(frozen=True)
class Message:
    """
    Represents a message as it is sent over the wire.
    """
    channel: str
    timestamp: float
    payload: 'typing.Any'


class Sender:
    """
    A sender allows messages to be sent to all of the recievers listening on a
    channel. Although it is instantiated with a set channel it is actually possible
    to send messages on any channel by building the message yourself and passing
    it to send_message.
    """

    def __init__(self, server: str, channel: str):
        self.publisher = context.socket(zmq.PUB)
        self.publisher.connect(server)
        self.channel = channel

    def send_message(self, message: Message):
        """
        Sends a built message object to all recievers. Note that channel used is
        specified by the message object rather than the sender.
        """
        self.publisher.send_multipart([
            message.channel.encode("utf-8"),
            msgpack.packb(message.timestamp),
            msgpack.packb(message.payload)
        ])

    def send(self, payload):
        """
        Wraps a payload in a message object and sends it on the sender's channel.
        """
        message = Message(self.channel, time.time(), payload)
        self.send_message(message)


class Receiver:
    """
    A reciever listens to a channel and recieves all messages sent to that channel.
    This filtering is based on only the beginning of the channel name, so for
    example a reciever listening to the channel 'foo' will also recieve messages
    sent to 'foobar', and a reciever listing to the channel '' will recieve all
    messages.
    """

    def __init__(self, server: str, channel: str):
        self.subscriber = context.socket(zmq.SUB)
        self.subscriber.connect(server)
        self.subscriber.setsockopt(zmq.SUBSCRIBE, channel.encode("utf-8"))

    def recv_message(self, timeout=None):
        """
        Recieves one message from a sender.

        If timeout is None this blocks until a message is recieved. Otherwise it
        waits for timeout milliseconds to recieve a message and returns None. A zero
        timeout is supported for nonblocking operation.
        """

        if self.subscriber.poll(timeout):
            channel, timestamp, payload = self.subscriber.recv_multipart()
            return Message(channel.decode("utf-8"), msgpack.unpackb(timestamp), msgpack.unpackb(payload))
        return None

    def recv(self, timeout=None):
        """
        Recieves the payload of one message from a sender, discarding metadata.

        If timeout is None this blocks until a message is recieved. Otherwise it
        waits for timeout milliseconds to recieve a message and returns None. A zero
        timeout is supported for nonblocking operation.
        """

        if message := self.recv_message(timeout):
            return message.payload
        return None
