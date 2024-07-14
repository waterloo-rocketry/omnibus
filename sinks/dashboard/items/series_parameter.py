from publisher import publisher
from pyqtgraph.parametertree.parameterTypes import ChecklistParameter, ListParameter


class SeriesListParameter(ListParameter):
    """A ListParameter for data series."""

    limits: list[str] = publisher.get_all_streams()

    def __init__(self):
        super().__init__(name='series',
                         type='list',
                         value=[],
                         limits=self.limits)
        publisher.register_stream_callback(self.setLimits)
    
    def setValue(self, value, blockSignal=None):
        if value != [] and value not in self.limits:
            publisher.ensure_exists(value)
            self.setLimits(publisher.get_all_streams())
        return super().setValue(value, blockSignal)
    
    def setLimits(self, limits):
        self.limits = limits
        return super().setLimits(limits)

class SeriesChecklistParameter(ChecklistParameter):
    """A ChecklistParameter for data series."""
    
    limits: list[str] = publisher.get_all_streams()

    def __init__(self):
        super().__init__(name='series',
                         type='list',
                         value=[],
                         limits=self.limits)
        publisher.register_stream_callback(self.setLimits)
    
    def setValue(self, values, blockSignal=None):
        if not isinstance(values, list):
            values = [values]
        for value in values:
            if value not in self.limits:
                publisher.ensure_exists(value)
                self.setLimits(publisher.get_all_streams())
        return super().setValue(values, blockSignal)
    
    def setLimits(self, limits):
        self.limits = limits
        return super().setLimits(limits)