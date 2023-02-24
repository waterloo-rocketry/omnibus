import re
import os

class CanlibMetadata:
    def __init__(self, fileName):
        self.dict = {}
        self.load_data(fileName)

    def load_data(self, fileName):
        pattern = r'^\s*\*?\s*(\w+)\s*:\s*(.*)$'
        dir_path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(dir_path, fileName)
        print(path)
        with open(path) as file:
            for line in file:
                match = re.match(pattern, line)
                if match:
                    msg_type = match.group(1)
                    msg_data = [token for token in match.group(2).split() if token != "None"]
                    self.dict[msg_type] = msg_data
        self.dict = dict(sorted(self.dict.items()))

    def getMessageTypes(self):
        return list(self.dict.keys())

    def getDataInfo(self, key):
        return self.dict.get(key, [])
