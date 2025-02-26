from dataclasses import dataclass
import socket
import time

import msgpack
import zmq
from datetime import datetime

from typing import Any, ClassVar

try:
    from . import server
except ImportError:
    # Python complains if we run `python -m omnibus` from the omnibus folder.
    # This works around that complaint.
    import server  # pyright: ignore[reportImplicitRelativeImport]

# Python also doesn't execute __main__ if we're in the omnibus folder.
# If that is the case (we were directly executed), start the server ourselves.
if __name__ == "__main__":
    try:
        server.server()
    except KeyboardInterrupt:
        pass


@dataclass(frozen=True)
class Message:
    """
    Represents a message as it is sent over the wire.
    """

    channel: str
    timestamp: float
    payload: Any


class OmnibusCommunicator:
    """
    Handles state shared between senders and receivers.
    """
    # These should've been initialized on __init__ and shouldn't change
    server_ip: ClassVar[str | None] = None
    context: ClassVar[zmq.Context[zmq.SyncSocket] | None] = None

    def __init__(self):
        if OmnibusCommunicator.context is None:
            OmnibusCommunicator.context = zmq.Context()
        if OmnibusCommunicator.server_ip is None:
            OmnibusCommunicator.server_ip = self._recv_ip()

    def _recv_ip(self) -> str:
        """
        Listen for a UDP broadcast from the server telling us its IP. If the
        broadcast isn't received, prompt to manually enter the IP.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:  # UDP
            # Allow the address to be re-used for when running multiple
            # components on the same machine
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(0.6)  # 0.6 second timeout
            sock.bind(("", server.BROADCAST_PORT))  # listen for broadcasts
            print("Listening for server IP...")
            while True:
                try:
                    data, (addr, _) = sock.recvfrom(16)
                    if data == b"omnibus":
                        print(f"Found {addr}")
                        return str(addr)
                except socket.timeout:
                    pass
                print("Could not detect server IP. Please ensure it is running.")
                if ip := input(
                    "Press enter to retry or manually enter the server IP: "
                ).strip():
                    return ip
                print("Retrying...")


class Sender(OmnibusCommunicator):
    """
    Allows messages to be sent to all of the receivers listening on the provided
    channel.
    """

    _publisher: zmq.SyncSocket

    def __init__(self):
        super().__init__()
        assert (
            OmnibusCommunicator.context is not None
            and OmnibusCommunicator.server_ip is not None
        )
        self._publisher = OmnibusCommunicator.context.socket(zmq.PUB)
        self._publisher.connect(
            f"tcp://{OmnibusCommunicator.server_ip}:{server.SOURCE_PORT}"
        )

    def send_message(self, message: Message) -> None:
        """
        Send a built message object to all receivers.

        Note that channel used is specified by the message object rather than
        the sender.
        """
        self._publisher.send_multipart(
            [
                message.channel.encode("utf-8"),
                msgpack.packb(message.timestamp),
                msgpack.packb(message.payload),
            ]
        )

    def send(self, channel: str, payload) -> None:
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

    :param *channels: All the channels the receiver should be listening on, pass each as
            individual parameters. Only the beginning of the name is matched.
    :param seconds_until_reconnect_attempt: OPTIONAL - Specify the number of seconds the
            Receiver should wait before attempting a reconnection when no messages
            are being received. Default value is 5 seconds. Keyword parameter only.
    """

    _channels: tuple[str, ...]
    # Keep track of last received message, only second granularity is needed
    # so time.time() is good enough on any platform
    _last_online_check: float
    _disconnected: bool
    _seconds_until_attempt_reconnect: int

    _subscriber: zmq.SyncSocket

    def __init__(self, *channels: str, seconds_until_reconnect_attempt: int = 5):
        """
        Listens to a number of channels and receives all messages sent to them.

        Filtering is based on only the beginning of the channel name, so for example
        a receiver listening to the channel 'foo' will also receive messages sent
        to 'foobar', and a receiver listing to the channel '' will receive all
        messages.

        :param *channels: All the channels the receiver should be listening on, pass each as
                individual parameters. Only the beginning of the name is matched. '' means all channels.
        :param seconds_until_reconnect_attempt: OPTIONAL - Specify the number of seconds the
                Receiver should wait before attempting a reconnection when no messages
                are being received. Default value is 5 seconds. Keyword parameter only.
        """
        super().__init__()
        self._last_online_check = time.time()
        self._channels = channels
        self._seconds_until_attempt_reconnect = seconds_until_reconnect_attempt
        self._disconnected = False
        self._connect()

    def _connect(self) -> None:
        """
        Create ZMQ subscriber and connect to server
        """
        assert ( 
            OmnibusCommunicator.server_ip is not None
            and OmnibusCommunicator.context is not None
        )
        self._subscriber = OmnibusCommunicator.context.socket(zmq.SUB)
        self._subscriber.connect(
            f"tcp://{OmnibusCommunicator.server_ip}:{server.SINK_PORT}"
        )
        for channel in self._channels:
            self._subscriber.setsockopt(zmq.SUBSCRIBE, channel.encode("utf-8"))

    def _check_online_and_reconnect(self, poll_result: int) -> None:
        """
        Check if the ZMQ socket is still online based on the last poll_result and the time elapsed since
        the last successful poll as compared to `self._seconds_until_attempt_reconnect`. Calls `self._reset()`
        if we are indeed offline (no message received for over `self._seconds_until_attempt_reconnect`).

        :param poll_result: Result from self._subscriber.poll(), where 0 means no message received, any other value
                means that a message was received.

        """
        if poll_result != 0:
            self._last_online_check = time.time()
            # If we were disconnected, print that we are now reconnected
            if self._disconnected:
                print(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] Omnibus Receiver is online!"
                )
            self._disconnected = False
            return
        # No message received
        if (
            time.time() - self._last_online_check
            >= self._seconds_until_attempt_reconnect
        ):
            print(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [WARN] "
                + f"({'All Channels' if self._channels[0] == '' else ','.join(channel for channel in self._channels)})"
                + " No messages received for a while, is Omnibus online?"
            )
            self._disconnected = True
            self._last_online_check = time.time()
            self._reset()

    def recv_message(self, timeout: int | None = None) -> Message | None:
        """
        Receive one message from a sender.

        If timeout is None this blocks until a message is received. Otherwise it
        waits for timeout milliseconds to receive a message and returns None. A
        zero timeout is supported for nonblocking operation.
        """
        # Ensure that we do still check for network loss even when timeout is large or infinite
        actual_timeout = (
            self._seconds_until_attempt_reconnect * 1000
            if timeout == None
            else min(timeout, self._seconds_until_attempt_reconnect * 1000)
        )
        elapsed_time_ms = 0  # only incremented if timeout is not infinite
        while timeout == None or elapsed_time_ms < timeout or timeout == 0:
            # 0 if no messages, something else if message received
            poll_result: int = self._subscriber.poll(timeout=actual_timeout)
            # Will attempt to reconnect here if reconnection timeout exceeded
            self._check_online_and_reconnect(poll_result)

            # If no message received:
            if poll_result == 0:
                if timeout == 0:
                    break
                if timeout is not None:
                    elapsed_time_ms += actual_timeout
                    # Below is slightly inaccurate if the timeout is very large,
                    # but if you have 5+ second timeouts I don't think 1ms matters
                    actual_timeout = min(timeout - elapsed_time_ms, actual_timeout)
                continue

            # If there is a message received, proceed below:
            channel, timestamp, payload = self._subscriber.recv_multipart()
            self._last_online_check = time.time()
            return Message(
                channel=channel.decode(encoding="utf-8"),
                timestamp=msgpack.unpackb(timestamp),
                payload=msgpack.unpackb(payload),
            )
        return None

    def recv(self, timeout: int | None = None) -> Any | None:
        """
        Receive the payload of one message from a sender, discarding metadata.

        If timeout is None this blocks until a message is received. Otherwise it
        waits for timeout milliseconds to receive a message and returns None. A
        zero timeout is supported for nonblocking operation.
        """

        if message := self.recv_message(timeout):
            return message.payload
        return None

    def _reset(self) -> None:
        """
        Restart the ZMQ Socket of this receiver instance. Called when the Receiver
        has not received any data for over a given number of seconds, specified
        by seconds_until_reconnect_attempt.
        """
        self._subscriber.close(linger=0)
        self._connect()
