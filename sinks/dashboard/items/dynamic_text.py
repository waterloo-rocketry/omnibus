from pyqtgraph.Qt.QtWidgets import QHBoxLayout, QLabel
from pyqtgraph.Qt.QtCore import QTimer, Qt
from pyqtgraph.parametertree.parameterTypes import ListParameter, ActionParameter, GroupParameter, ColorParameter

from publisher import publisher
from .dashboard_item import DashboardItem
from .registry import Register

EXPIRED_TIME = 1 # time in seconds after which data "expires"

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

        self.expired_timeout = QTimer()
        self.expired_timeout.setSingleShot(True)
        self.expired_timeout.timeout.connect(self.expire)
        self.expired_timeout.start(EXPIRED_TIME * 1000)

        series = self.parameters.param('series').value()
        self.offset = self.parameters.param('offset').value()
        publisher.subscribe(series, self.on_data_update)

        self.widget = QLabel()
        self.layout.addWidget(self.widget)

        # Apply initial stylesheet
        self.on_font_change(None, self.parameters.param("font size").value())

    def add_parameters(self):
        font_param = {'name': 'font size', 'type': 'int', 'value': 12}
        series_param = ListParameter(name='series',
                                          type='list',
                                          default="",
                                          limits=publisher.get_all_streams())
        offset_param =  {'name': 'offset', 'type': 'float', 'value': 0}
        new_param_button = ActionParameter(name='add_new', 
                                                title="Add New")
        return [font_param, series_param, offset_param, new_param_button]

    def on_series_change(self, _, value):
        publisher.unsubscribe_from_all(self.on_data_update)
        publisher.subscribe(value, self.on_data_update)

    def on_data_update(self, _, payload):
        time, data = payload
        if isinstance(data, int):
            self.widget.setText(f"{data + self.offset:.0f}")
        elif isinstance(data, float):
            self.widget.setText(f"{data + self.offset:.3f}")
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
        self.expired_timeout.start(EXPIRED_TIME * 1000)
        self.resize(10, 10) # trigger size update

    def condition_true(self, condition: GroupParameter):
        comparison = condition.childs[0].value()
        condition_value = condition.childs[1].value()
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
        self.setStyleSheet("color: gray")

    def on_font_change(self, _, fsize):
        self.widget.setStyleSheet("font-size: {}px".format(fsize))

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

    @staticmethod
    def get_name():
        return "Dynamic Text"

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update)
