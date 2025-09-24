from publisher import publisher
from pyqtgraph.parametertree.parameterTypes import ChecklistParameter, ListParameter


class SeriesListParameter(ListParameter):
    """A ListParameter for data series."""

    def __init__(self):
        self.limits: list[str] = publisher.get_all_streams()
        super().__init__(name='series',
                         type='list',
                         value=[],
                         limits=self.limits)

    def refresh_limits(self):
        self.setLimits(publisher.get_all_streams())

    def setValue(self, value, blockSignal=None):
        if value != [] and value not in self.limits:
            publisher.ensure_exists(value)
            self.refresh_limits()
        return super().setValue(value, blockSignal)
    
    def setLimits(self, limits):
        self.limits = limits
        return super().setLimits(limits)

class SeriesChecklistParameter(ChecklistParameter):
    """A ChecklistParameter for data series."""
    
    def __init__(self):
        self.limits: list[str] = publisher.get_all_streams()
        super().__init__(name='series',
                         type='list',
                         value=[],
                         limits=self.limits)
    
    def refresh_limits(self):
        self.setLimits(publisher.get_all_streams())

    def setValue(self, values, blockSignal=None):
        if not isinstance(values, list):
            values = [values]
        for value in values:
            if value not in self.limits:
                publisher.ensure_exists(value)
                self.refresh_limits()
        return super().setValue(values, blockSignal)
    
    def setLimits(self, limits):
        self.limits = limits
        return super().setLimits(limits)
