from typing import Any, Callable

StreamCallback = Callable[[str, Any], None]
StreamListCallback = Callable[[list[str]], None]
ClockCallback = Callable[[int], None]


class Publisher:
    """
    The core data bus of the dashboard.

    This class holds a number number of streams. Users may
    subscribe to these streams to recieve notifications
    upon updates. This is done by providing a callback, which
    is called when the data is updated.
    """

    streams: dict[str, list[StreamCallback]]
    stream_update_callbacks: list[StreamListCallback]
    ticks: int
    clock_callbacks: list[tuple[int, int, ClockCallback]]

    def __init__(self) -> None:
        self.streams = {}
        self.stream_update_callbacks = []
        self.ticks = 0
        self.clock_callbacks = []

    def register_stream_callback(self, cb: StreamListCallback) -> None:
        self.stream_update_callbacks.append(cb)

    def get_all_streams(self) -> list[str]:
        ret_val = list(self.streams.keys())
        ret_val.sort()
        return ret_val

    def subscribe(self, stream: str, callback: StreamCallback) -> None:
        self.ensure_exists(stream)
        self.streams[stream].append(callback)

    def unsubscribe_from_all(self, callback: Callable[..., None]) -> None:
        for stream in self.streams:
            if callback in self.streams[stream]:
                self.streams[stream].remove(callback)

        self.clock_callbacks = [(s, i, c) for (s, i, c) in self.clock_callbacks if c != callback]

    def update(self, stream: str, payload: Any) -> None:
        self.ensure_exists(stream)
        for callback in self.streams[stream]:
            callback(stream, payload)

    def subscribe_clock(self, interval: int, callback: ClockCallback) -> None:
        self.clock_callbacks.append((self.ticks, interval, callback))

    def update_clock(self) -> None:
        self.ticks += 1
        for start, interval, cb in self.clock_callbacks:
            if (self.ticks + start) % interval == 0:
                cb(self.ticks)

    def ensure_exists(self, stream: str) -> None:
        if stream not in self.streams:
            self.streams[stream] = []
            streams = list(self.streams.keys())
            streams.sort()
            for cb in self.stream_update_callbacks:
                cb(streams)


publisher = Publisher()
