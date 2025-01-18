class Publisher:
    """
    The core data bus of the dashboard.

    This class holds a number number of streams. Users may
    subscribe to these streams to recieve notifications
    upon updates. This is done by providing a callback, which
    is called when the data is updated.
    """

    def __init__(self):
        self.streams = {}
        self.stream_update_callbacks = []
        self.ticks = 0
        self.clock_callbacks = []

    def register_stream_callback(self, cb):
        self.stream_update_callbacks.append(cb)

    def get_all_streams(self):
        ret_val = list(self.streams.keys())
        ret_val.sort()
        return ret_val

    def subscribe(self, stream, callback):
        self.ensure_exists(stream)
        self.streams[stream].append(callback)

    def unsubscribe_from_all(self, callback):
        for stream in self.streams:
            if callback in self.streams[stream]:
                self.streams[stream].remove(callback)

        if callback in self.clock_callbacks:
            self.clock_callbacks.remote(callback)

    def update(self, stream, payload):
        self.ensure_exists(stream)
        for callback in self.streams[stream]:
            callback(stream, payload)

    def subscribe_clock(self, interval, callback):
        self.clock_callbacks.append((self.ticks, interval, callback))

    def update_clock(self):
        self.ticks += 1
        for start, interval, cb in self.clock_callbacks:
            if (self.ticks + start) % interval == 0:
                cb(self.ticks)

    def ensure_exists(self, stream):
        if stream not in self.streams:
            self.streams[stream] = []
            streams = list(self.streams.keys())
            streams.sort()
            for cb in self.stream_update_callbacks:
                cb(streams)


publisher = Publisher()
