import re
import os

class CanlibMetadata:
    def __init__(self, fileName):
        self.info = {}
        self.load_data(fileName)

    def load_data(self, fileName):
        pattern = r'^\s*\*?\s*(\w+)\s*:\s*(.*)$'
        dir_path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(dir_path, fileName)
        with open(path) as file:
            for line in file:
                match = re.match(pattern, line)
                if match:
                    msg_type = match.group(1)
                    msg_data = [token for token in match.group(2).split() if token != "None"]

                    """
                    HARD CODEY STUFF INCOMING
                    tldr for some bytes, the comment labels is "ALT_ARM_STATE & #"
                    or DEBUG_LEVEL | LINUM_H
                    which ruins the clean split() sol so here's my hacky fix
                    """
                    i = 1
                    while i < len(msg_data) - 1:
                        if msg_data[i]=='&' or msg_data[i]=='|':
                            msg_data[i-1] = " ".join(msg_data[i-1:i+2])
                            del msg_data[i:i+2]
                        else:
                            i += 1
                    self.info[msg_type] = msg_data
        self.info = dict(sorted(self.info.items()))

    def getMessageTypes(self):
        return list(self.info.keys())

    def getDataInfo(self, key):
        return self.info.get(key, [])
