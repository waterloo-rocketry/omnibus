class Register:
    item_list = []

    def __init__(self, item):
        Register.item_list.append(item)


def get_items():
    return Register.item_list
