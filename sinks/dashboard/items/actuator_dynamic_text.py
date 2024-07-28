from pyqtgraph.Qt.QtWidgets import QHBoxLayout, QLabel, QCompleter
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

from ops_valve_definitions import actuator_id_closed_states

EXPIRED_TIME = 1.2  # time in seconds after which data "expires"


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
class ActuatorDynamicTextItem(DashboardItem):
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
        self.parameters.param('vertical padding').sigValueChanged.connect(self.on_vpad_change)
        self.parameters.param('horizontal padding').sigValueChanged.connect(self.on_hpad_change)

        self.expired_timeout = QTimer()
        self.expired_timeout.setSingleShot(True)
        self.expired_timeout.timeout.connect(self.expire)
        self.expired_timeout.start(int(EXPIRED_TIME * 1000))

        series = self.parameters.param('series').value()
        self.offset = self.parameters.param('offset').value()
        publisher.subscribe(series, self.on_data_update)

        self.widget = QLabel()
        self.layout.addWidget(self.widget)

        # Apply initial stylesheet
        self.on_font_change(None, self.parameters.param("font size").value())

        self.buffer_size = self.parameters.param('buffer size').value()
        self.buffer = []

    def add_parameters(self):
        font_param = {'name': 'font size', 'type': 'int', 'value': 12}
        series_param = SimpleParameter(name='series', type='str', default="")
        series_param.itemClass = AutocompleteParameterItem
        offset_param = {'name': 'offset', 'type': 'float', 'value': 0}
        buffer_size_param = {'name': 'buffer size', 'type': 'int', 'value': 1}
        new_param_button = ActionParameter(name='add_new',
                                                title="Add New")

        vpad_param = {'name': 'vertical padding', 'type': 'int', 'value': 10}
        hpad_param = {'name': 'horizontal padding', 'type': 'int', 'value': 10}

        return [font_param, series_param, offset_param, buffer_size_param, 
                 vpad_param, hpad_param, new_param_button]

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
            str_data = str(data)

            is_actuator_series = False
            curr_series = self.parameters.param('series').value()
            print(curr_series)
            keys = list(actuator_id_closed_states.keys())
            print(keys)
            for itm in keys:
                is_actuator_series |= curr_series.__contains__(itm) 
                key = itm
                if is_actuator_series: break
                # print(is_actuator_series)
                

            if is_actuator_series:
                if actuator_id_closed_states[key] == 'ACTUATOR_OFF':
                    if str_data == "ACTUATOR_OFF":
                        str_data = "CLOSED: " + str_data
                    else: str_data = "OPEN: " + str_data
                else:
                    if str_data == "ACTUATOR_OFF":
                        str_data = "OPEN: " + str_data
                    else: str_data = "CLOSED: " + str_data

            self.widget.setText(str_data)

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
        self.resize(10, 10)  # trigger size update

    def condition_true(self, condition: GroupParameter):
        comparison = condition.childs[0].value()
        condition_value = str(condition.childs[1].value())
        data = self.widget.text()
        match comparison:
            case '==':
                return data == condition_value
            case '<':
                return data < condition_value
            case '>':
                return data > condition_value
            case '<=':
                return data <= condition_value
            case '>=':
                return data >= condition_value
            case '!=':
                return data != condition_value
            case _:
                return False

    def expire(self):
        self.setStyleSheet("color: red")

    def on_font_change(self, _, fsize):
        self.widget.setStyleSheet(f"font-size: {fsize}px")

    def on_offset_change(self, _, offset):
        self.offset = offset

    def on_add_new_change(self, _):
        # Increment number of conditions and get string representation
        self.condition_count += 1
        cond_count_str = str(self.condition_count)

        # Insert a new GroupParameter into the ParameterTree
        #   with 3 children: a condition (</>, <=/>=, =/!=),
        #                    a value,
        #                    a ColorParameter
        condition_label = 'Condition ' + cond_count_str
        self.parameters.insertChild(pos=(len(self.parameters.childs)-1),
                                    child=GroupParameter(name='condition_label' + cond_count_str,
                                                         title=condition_label))

        condition_reference = self.parameters.param('condition_label' + cond_count_str)
        list_of_comparisons = ['>', '<', '>=', '<=', '==', '!=']
        condition_reference.addChild(child=ListParameter(name='condition',
                                                         type='list',
                                                         default='==',
                                                         limits=list_of_comparisons))
        condition_reference.addChild(child={'name': 'value',
                                            'type': 'float',
                                            'value': 0})
        condition_reference.addChild(child=ColorParameter(name='color'))

    def on_buffer_size_change(self, _, bufsize):
        self.buffer_size = bufsize
        self.buffer = []

    def on_vpad_change(self, param, value):
        hpad = self.parameters.param('horizontal padding').value()
        # int left, int top, int right, int bottom
        self.layout.setContentsMargins(hpad, value, hpad, value)
    
    def on_hpad_change(self, param, value):
        vpad = self.parameters.param('vertical padding').value()
        # int left, int top, int right, int bottom
        self.layout.setContentsMargins(value, vpad, value, vpad)

    @staticmethod
    def get_name():
        return "Actuator Dynamic Text"

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update)
