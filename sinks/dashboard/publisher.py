class Publisher:
    """
    Abstract class acting as the Subject of Observation from observers.
    """

    def __init__(self):
        self.streams = {}

    def get_all_stream(self, _type=""):
        return_stream = []
        for key in list(self.streams.keys()):
            if key.startswith(_type):
                return_stream.append(key)
        return return_stream

    def subscribe(self, stream, observer):
        """
        An observer is a dashboard item that cares
        about data updates. Adding an observer
        means adding an item to be notified
        when the data is updated
        """
        if stream not in self.streams:
            self.streams[stream] = []
        self.streams[stream].append(observer)

    def unsubscribe_from_all(self, observer):
        for stream in self.streams:
            if observer in self.streams[stream]:
                self.streams[stream].remove(observer)

    def update(self, stream, payload):
        if stream not in self.streams:
            self.streams[stream] = []
        for observer in self.streams[stream]:
            observer.on_data_update(payload)


publisher = Publisher()
