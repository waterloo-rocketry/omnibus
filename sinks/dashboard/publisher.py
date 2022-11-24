class Publisher:
    """
    Abstract class acting as the Subject of Observation from observers.
    """

    def __init__(self):
        self.serieses = {}

    def get_all_series(self, _type=""):
        return_series = []
        for key in list(self.serieses.keys()):
            if key.endswith(_type):
                return_series.append(key)
        return return_series

    def subscribe(self, series, observer):
        """
        An observer is a dashboard item that cares
        about data updates. Adding an observer
        means adding an item to be notified
        when the data is updated
        """
        if series not in self.serieses:
            self.serieses[series] = []
        self.serieses[series].append(observer)

    def unsubscribe_from_all(self, observer):
        for series in self.serieses:
            if observer in self.serieses[series]:
                self.serieses[series].remove(observer)

    def update(self, series, payload):
        if series not in self.serieses:
            self.serieses[series] = []
        for observer in self.serieses[series]:
            observer.on_data_update(payload)


publisher = Publisher()
