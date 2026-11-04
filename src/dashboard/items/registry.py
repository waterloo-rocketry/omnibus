from typing import Any


class Register:
    item_list: list[type[Any]] = []

    def __init__(self, item: type[Any]) -> None:
        Register.item_list.append(item)


def get_items() -> list[type[Any]]:
    return Register.item_list