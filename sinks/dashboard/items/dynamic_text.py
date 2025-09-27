from collections import OrderedDict
import json

from pyqtgraph.Qt.QtWidgets import QHBoxLayout, QLabel, QCompleter, QSizePolicy
from pyqtgraph.Qt.QtCore import QTimer, Qt
from pyqtgraph.parametertree.parameterTypes import (
    SimpleParameter,
    StrParameterItem,
    ListParameter,
    ActionParameter,
    GroupParameter,
    ColorParameter
)

from publisher import publisher
from .dashboard_item import DashboardItem
from .registry import Register
from .series_parameter import SeriesListParameter

import operator

EXPIRED_TIME = 2.5  # time in seconds after which data "expires"

class AutocompleteParameterItem(StrParameterItem):
    completer = QCompleter(publisher.get_all_streams())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        publisher.register_stream_callback(self.update_completions)

    def makeWidget(self):
        w = super().makeWidget()
        self.completer = QCompleter(publisher.get_all_streams())
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        w.setCompleter(AutocompleteParameterItem.completer)
        return w

    @staticmethod
    def update_completions(streams):
        AutocompleteParameterItem.completer.model().setStringList(streams)


publisher.register_stream_callback(AutocompleteParameterItem.update_completions)


@Register
class DynamicTextItem(DashboardItem):
    def __init__(self, *args):
        # Call this in **every** dash item constructor
        super().__init__(*args)

        self.condition_count = 0
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # Specify the layout
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.parameters.param('series').sigValueChanged.connect(self.on_series_change)
        self.parameters.param('font size').sigValueChanged.connect(self.on_font_change)
        self.parameters.param('offset').sigValueChanged.connect(self.on_offset_change)
        self.parameters.param('add_new').sigActivated.connect(self.on_add_new_change)
        self.parameters.param('buffer size').sigValueChanged.connect(self.on_buffer_size_change)
        self.parameters.param('dynamic_size_policy').sigValueChanged.connect(self.update_size_policy)

        self.expired_timeout = QTimer()
        self.expired_timeout.setSingleShot(True)
        self.expired_timeout.timeout.connect(self.expire)
        self.expired_timeout.start(int(EXPIRED_TIME * 1000))

        series = self.parameters.param('series').value()
        self.offset = self.parameters.param('offset').value()
        publisher.subscribe(series, self.on_data_update)

        self.widget = QLabel()
        self.update_size_policy(None)  # Set initial size policy
        self.widget.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.widget)

        # Apply initial stylesheet
        self.on_font_change(None, self.parameters.param("font size").value())

        self.buffer_size = self.parameters.param('buffer size').value()
        self.buffer = []

        # Restore the conditions if any exist
        if len(args) == 2:
            _, params = args
            try:
                state = json.loads(params, object_pairs_hook=OrderedDict)
                conditions = [(k, v["children"]) for k, v in state["children"].items() if "children" in v and v["children"]]
                for condition_name, condition_states in conditions:
                    self.add_condition(condition_name, condition_states["condition"]["value"],
                                       condition_states["value"]["value"], condition_states["color"]["value"])
            except (json.JSONDecodeError, KeyError, TypeError) as e: 
                print("Unable to restore condition:", e)
                pass 

    def add_condition(self, condition_name=None, condition_state="==", condition_value=0, condition_color = None):
        # Increment number of conditions and get string representation
        self.condition_count += 1
        cond_count_str = str(self.condition_count)

        # Insert a new GroupParameter into the ParameterTree
        #   with 3 children: a condition (</>, <=/>=, =/!=),
        #                    a value,
        #                    a ColorParameter
        condition_label = condition_name if condition_name else 'condition_label' + cond_count_str
        self.parameters.insertChild(pos=(len(self.parameters.childs)-1),
                                    child=GroupParameter(name='condition_label' + cond_count_str,
                                                         title=condition_label))

        condition_reference = self.parameters.param(condition_label)
        list_of_comparisons = ['>', '<', '>=', '<=', '==', '!=', 'contains']
        condition_reference.addChild(child=ListParameter(name='condition',
                                                         type='list',
                                                         default=condition_state,
                                                         limits=list_of_comparisons))
        condition_reference.addChild(child={'name': 'value',
                                            'type': 'str',
                                            'value': condition_value})
        condition_reference.addChild(child=ColorParameter(name='color', value=condition_color))

    def update_size_policy(self, _):
        if self.parameters.param('dynamic_size_policy').value():
            self.widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        else:
            self.widget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

    def add_parameters(self):
        font_param = {'name': 'font size', 'type': 'int', 'value': 12}
        series_param = SeriesListParameter()
        offset_param = {'name': 'offset', 'type': 'float', 'value': 0}
        buffer_size_param = {'name': 'buffer size', 'type': 'int', 'value': 1}
        dynamic_size_policy_param = {'name': 'dynamic_size_policy', 'type': 'bool', 'value': False, 'title': 'dynamic size'}
        new_param_button = ActionParameter(name='add_new',
                                                title="Add New")
        return [dynamic_size_policy_param, font_param, series_param, offset_param, buffer_size_param, new_param_button]

    def on_series_change(self, _, value):
        publisher.unsubscribe_from_all(self.on_data_update)
        publisher.subscribe(value, self.on_data_update)

    def on_data_update(self, _, payload):
        time, data = payload

        self.buffer.append(data)
        if len(self.buffer) > self.buffer_size:
            self.buffer.pop(0)

        if isinstance(data, int):
            value = sum(self.buffer)/len(self.buffer)
            self.widget.setText(f"{value + self.offset:.0f}")
        elif isinstance(data, float):
            value = sum(self.buffer)/len(self.buffer)
            self.widget.setText(f"{value + self.offset:.3f}")
        else:
            self.widget.setText(str(data))

        # If there are conditions, change colour based on them
        #   else, set background to the default color
        for i in range(self.condition_count):
            condition_reference = self.parameters.param('condition_label' + str(i + 1))
            if self.condition_true(condition_reference):
                background_color = condition_reference.childs[2].value().name()
                self.setStyleSheet('background: ' + background_color)
                break
        else:
            self.setStyleSheet('')

        self.expired_timeout.stop()
        self.expired_timeout.start(int(EXPIRED_TIME * 1000))

    def condition_true(self, condition: GroupParameter):
        comparison = str(condition.childs[0].value())
        condition_value = str(condition.childs[1].value())
        data_text = self.widget.text()
        
        ops = {
            '==': operator.eq,
            '!=': operator.ne,
            '<': operator.lt,
            '>': operator.gt,
            '<=': operator.le,
            '>=': operator.ge,
        }

        str_only_ops = {
            "contains": operator.contains
        }

        if comparison in str_only_ops:
            op_func = str_only_ops[comparison]
            return bool(op_func(data_text.lower(), condition_value.lower()))

        if comparison not in ops:
            return False
        
        op_func = ops[comparison]

        try:
            return bool(op_func(float(data_text), float(condition_value)))
        except (ValueError, TypeError):
            return bool(op_func(data_text.lower(), condition_value.lower()))
    
    def expire(self):
        self.setStyleSheet("color: red")

    def on_font_change(self, _, fsize):
        self.widget.setStyleSheet(f"font-size: {fsize}px")

    def on_offset_change(self, _, offset):
        self.offset = offset

    def on_add_new_change(self, _):
        self.add_condition()

    def on_buffer_size_change(self, _, bufsize):
        self.buffer_size = bufsize
        self.buffer = []

    @staticmethod
    def get_name():
        return "Dynamic Text"

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update)
