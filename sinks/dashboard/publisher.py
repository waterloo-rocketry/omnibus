class Publisher:
    """
    Abstract class acting as the Subject of Observation from observers.
    """

    def __init__(self):
        self.serieses = {}
        self.canserieses = {}

    def get_CAN_series(self):
        return self.canserieses.keys()

    def get_DAQ_series(self):
        return self.serieses.keys()

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
