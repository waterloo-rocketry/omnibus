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

    def get_all_streams(self):
        ret_val = list(self.streams.keys())
        ret_val.sort()
        return ret_val

    def subscribe(self, stream, callback):
        if stream not in self.streams:
            self.streams[stream] = []
        self.streams[stream].append(callback)

    def unsubscribe_from_all(self, callback):
        for stream in self.streams:
            if callback in self.streams[stream]:
                self.streams[stream].remove(callback)

    def update(self, stream, payload):
        if stream not in self.streams:
            self.streams[stream] = []
        for callback in self.streams[stream]:
            callback(stream, payload)


publisher = Publisher()
