from publisher import publisher


class Subscriber():
    def __init__(self):
        self.subscribed_subjects = []

    def subscribe_to(self, subject):
        """
        Ensures that whenever a series' data is updated,
        the on_data_update method is called
        """
        publisher.subscribe(subject, self)
        self.subscribed_subjects.append(subject)

    def unsubscribe_to_all(self):
        """
        A helper function, designed to unsubscribe 
        this dash item from all series its subscribed 
        to
        """
        publisher.unsubscribe_from_all(self)

    def on_data_update(self, series):
        """
        Whenever data is updated in a series that we are subscribed
        to, this method is called. The series that was updated is supplied
        as a parameter
        """
        pass
