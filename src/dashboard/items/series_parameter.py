from publisher import publisher
from pyqtgraph.parametertree.parameterTypes import ChecklistParameter, ListParameter  # pyright: ignore[reportMissingTypeStubs]
from typing import Any, cast


def _all_streams() -> list[str]:
    return publisher.get_all_streams()


class SeriesListParameter(ListParameter):
    """A ListParameter for data series."""

    def __init__(self) -> None:
        self.limits: list[str] = _all_streams()
        super().__init__(name='series', type='list', value=[], limits=self.limits)  # pyright: ignore[reportUnknownMemberType]

    def refresh_limits(self) -> None:
        self.setLimits(_all_streams())

    def setValue(self, value: Any, blockSignal: Any | None = None) -> Any:
        if value != [] and value not in self.limits:
            cast(Any, publisher).ensure_exists(value)
            self.refresh_limits()
        return cast(Any, super()).setValue(value, blockSignal)

    def setLimits(self, limits: list[str]) -> None:
        self.limits = limits
        return cast(Any, super()).setLimits(limits)

class SeriesChecklistParameter(ChecklistParameter):
    """A ChecklistParameter for data series."""

    def __init__(self) -> None:
        self.limits: list[str] = _all_streams()
        super().__init__(name='series', type='list', value=[], limits=self.limits)  # pyright: ignore[reportUnknownMemberType]

    def refresh_limits(self) -> None:
        self.setLimits(_all_streams())

    def setValue(self, value: Any, blockSignal: Any | None = None) -> Any:
        if not isinstance(value, list):
            value = [value]
        for v in cast(list[Any], value):
            if v not in self.limits:
                cast(Any, publisher).ensure_exists(v)
                self.refresh_limits()
        return cast(Any, super()).setValue(value, blockSignal)

    def setLimits(self, limits: list[str]) -> None:
        self.limits = limits
        return cast(Any, super()).setLimits(limits)
