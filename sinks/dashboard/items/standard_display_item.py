from publisher import publisher
from .dashboard_item import DashboardItem
from .registry import Register

@Register
class StandardDisplayItem (DashboardItem):
    def __init__(self, *args):
        super().__init__(*args)

    def add_parameters(self):
        return []

    @staticmethod
    def get_name():
        return "Standard Display Item"
    
    def on_delete(self):
        publisher.unsusbcribe_from_all(self.on_data_update)