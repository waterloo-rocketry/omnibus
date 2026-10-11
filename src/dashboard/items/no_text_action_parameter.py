from pyqtgraph.parametertree.parameterTypes import ActionParameter, ActionParameterItem  # pyright: ignore[reportMissingTypeStubs]
from pyqtgraph.parametertree import Parameter  # pyright: ignore[reportMissingTypeStubs]

class NoTextActionParameterItem(ActionParameterItem):
    """An action parameter item that works around
    https://github.com/pyqtgraph/pyqtgraph/issues/2380.
    This avoids the text displaying twice on MacOS dark mode.
    """
    def __init__(self, param: Parameter, depth: int):
        super().__init__(param, depth)
        self.setText(0, "")


class NoTextActionParameter(ActionParameter):
    """An action parameter that works around a rendering bug."""
    itemClass = NoTextActionParameterItem
