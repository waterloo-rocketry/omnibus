from typing import List, Callable, Any, Union, Tuple


class Publisher:
    """
    The core data bus of the dashboard. 

    This class holds a number of streams. Users may
    subscribe to these streams to receive notifications 
    upon updates. This is done by providing a callback, which
    is called when the data is updated.
    """

    def __init__(self) -> None:
        self.streams: dict[str, List[Callable[[str, Any], None]]] = {}
        self.stream_update_callbacks: List[Callable[[List[str]], None]] = []

    def register_stream_callback(self, cb: Callable[[List[str]], None]) -> None:
        self.stream_update_callbacks.append(cb)

    def get_all_streams(self) -> List[str]:
        ret_val: List[str] = list(self.streams.keys())
        ret_val.sort()
        return ret_val

    def subscribe(self, stream: str, callback: Callable[[str, Any], None]) -> None:
        self.ensure_exists(stream)
        self.streams[stream].append(callback)

    def unsubscribe_from_all(self, callback: Callable[[str, Any], None]) -> None:
        for stream in self.streams:
            if callback in self.streams[stream]:
                self.streams[stream].remove(callback)

    def update(self, stream: str, payload: Any) -> None:
        self.ensure_exists(stream)
        for callback in self.streams[stream]:
            callback(stream, payload)

    def ensure_exists(self, stream: str) -> None:
        if stream not in self.streams:
            self.streams[stream] = []
            streams: List[str] = list(self.streams.keys())
            streams.sort()
            for cb in self.stream_update_callbacks:
                cb(streams)


publisher: Publisher = Publisher()
