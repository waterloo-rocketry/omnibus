from dataclasses import dataclass
import socket
import sys
import time
import typing

import msgpack
import zmq
from datetime import datetime

try:
    from . import server
except ImportError:
    # Python complains if we run `python -m omnibus` from the omnibus folder.
    # This works around that complaint.
    import server  # pyright: ignore reportImplicitRelativeImport

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
    payload: typing.Any


class OmnibusCommunicator:
    """
    Handles state shared between senders and receivers.
    """

    server_ip = None
    context = None

    def __init__(self):
        if OmnibusCommunicator.context is None:
            OmnibusCommunicator.context = zmq.Context()
        if OmnibusCommunicator.server_ip is None:
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
            sock.bind(("", server.BROADCAST_PORT))  # listen for broadcasts
            print("Listening for server IP...")
            while True:
                try:
                    data, (addr, _) = sock.recvfrom(16)
                    if data == b"omnibus":
                        print(f"Found {addr}")
                        return addr
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

    def __init__(self):
        super().__init__()
        try:
            assert (
                OmnibusCommunicator.context != None
                and OmnibusCommunicator.server_ip != None
            )
            self.publisher = OmnibusCommunicator.context.socket(zmq.PUB)
            self.publisher.connect(
                f"tcp://{OmnibusCommunicator.server_ip}:{server.SOURCE_PORT}"
            )
            print(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] Omnibus sending to {OmnibusCommunicator.server_ip}"
            )
        except AssertionError:
            print(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] Initialization failure! Has the Omnibus IP and context been initialized?",
                file=sys.stderr,
            )
            raise RuntimeError(
                "Core Library Initialization Failed!"
            )  # Just in case context / ip gets set to None for some reason at runtime

    def send_message(self, message: Message):
        """
        Send a built message object to all receivers.

        Note that channel used is specified by the message object rather than
        the sender.
        """
        try:
            assert self.publisher != None
            self.publisher.send_multipart(
                [
                    message.channel.encode("utf-8"),
                    msgpack.packb(message.timestamp),
                    msgpack.packb(message.payload),
                ]
            )
        except AssertionError:
            print(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] Read Fail! Socket has not been initialized!",
                file=sys.stderr,
            )
            raise RuntimeError("Sender: Send before initialization")

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

    :param *channels: All the channels the receiver should be listening on, pass each as
            individual parameters. Only the beginning of the name is matched.
    :param seconds_until_reconnect_attempt: OPTIONAL - Specify the number of seconds the
            Receiver should wait before attempting a reconnection when no messages
            are being received. Default value is 5 seconds. Keyword parameter only.
    """

    ## PRIVATE PROPERTIES ##
    _channels: tuple[str, ...]
    # Keep track of last received message, only second granularity is needed
    # so time.time() is good enough on any platform
    _last_online_check: float
    _disconnected: bool
    _seconds_until_attempt_reconnect: int
    ## END PRIVATE PROPERTIES ##

    subscriber: zmq.SyncSocket | None = None

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
        print(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] Omnibus receiving from {OmnibusCommunicator.server_ip}"
        )

    def _connect(self):
        """
        Create ZMQ subscriber and connect to server
        """
        try:
            assert (
                OmnibusCommunicator.server_ip != None
                and OmnibusCommunicator.context != None
            )
            self.subscriber = OmnibusCommunicator.context.socket(zmq.SUB)
            self.subscriber.connect(
                f"tcp://{OmnibusCommunicator.server_ip}:{server.SINK_PORT}"
            )
            for channel in self._channels:
                self.subscriber.setsockopt(zmq.SUBSCRIBE, channel.encode("utf-8"))
        except AssertionError:
            print(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] Initialization failure! Has the Omnibus IP and context been initialized?",
                file=sys.stderr,
            )
            raise RuntimeError(
                "Omnibus: Core Library Initialization Failed!"
            )  # Just in case context / ip gets set to None for some reason at runtime
        except:
            print(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [WARN] Unable to connect to {OmnibusCommunicator.server_ip}!"
            )


    def _check_online_and_reconnect(self, poll_result: int) -> None:
        if poll_result != 0:
            self._last_online_check = time.time()
            if (
                self._disconnected
            ):  # If we were disconnected, print that we are now reconnected
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
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [WARN] ({'All Channels' if self._channels[0] == '' else ','.join(channel for channel in self._channels)}) No messages received for a while, is Omnibus online?"
            )
            self._disconnected = True
            self._last_online_check = time.time()
            self._reset()
            

    def recv_message(self, timeout: int | None = None):
        """
        Receive one message from a sender.

        If timeout is None this blocks until a message is received. Otherwise it
        waits for timeout milliseconds to receive a message and returns None. A
        zero timeout is supported for nonblocking operation.
        """
        try:
            assert (
                self.subscriber != None
            )  # Ensure subscriber is actually ready to receive, should never trigger in theory
            actual_timeout = ( # Ensure that we do still check for network loss even when timeout is large or infinite
                        self._seconds_until_attempt_reconnect * 1000
                        if timeout == None
                        else min(timeout, self._seconds_until_attempt_reconnect * 1000)
                    )
            i = 0
            while timeout == None or i < timeout:
                time_a = time.perf_counter()
                poll_result = self.subscriber.poll(
                    timeout=actual_timeout
                )
                time_b = time.perf_counter()
                t = time_b-time_a

                self._check_online_and_reconnect(poll_result) # Will attempt to reconnect here if reconnection timeout exceeded
                if poll_result == 0:  # No message received
                    if timeout == 0:
                        break
                    if (timeout != None):
                        i += actual_timeout # + 1 to prevent being stuck in the loop if timeout == 0
                        # Below is slightly inaccurate if the timeout is very large, but if you have 5+ second timeouts I don't think 1ms matters
                        actual_timeout: int = min(timeout - i, actual_timeout) 
                    continue
                # If there is a message received, proceed below
                channel, timestamp, payload = self.subscriber.recv_multipart()
                self._last_online_check = time.time()
                return Message(
                    channel=channel.decode(encoding="utf-8"),
                    timestamp=msgpack.unpackb(timestamp),
                    payload=msgpack.unpackb(payload),
                )
        except AssertionError:
            print(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] Read Fail! Socket has not been initialized!",
                file=sys.stderr,
            )
        return None

    def recv(self, timeout: int | None = None):
        """
        Receive the payload of one message from a sender, discarding metadata.

        If timeout is None this blocks until a message is received. Otherwise it
        waits for timeout milliseconds to receive a message and returns None. A
        zero timeout is supported for nonblocking operation.
        """

        if message := self.recv_message(timeout):
            return message.payload
        return None

    def _reset(self):
        """
        Restart the ZMQ Socket of this receiver instance. Called when the Receiver
        has not received any data for over a given number of seconds, specified
        by seconds_until_reconnect_attempt.
        """
        print("Reset!")
        if self.subscriber != None:
            self.subscriber.close(linger=0)
            self.subscriber = None  # Prevent receiver from attempting to read from socket while it's closed.
        self._connect()

