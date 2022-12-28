item_list = []
print("CLEARED ITEM LIST")
print("======================================================================")

class Register:

    def __init__(self, item):
        print(f"INIT: {item}")
        print(f"ITEM LIST: {item_list}")
        item_list.append(item)
        print(f"ITEM LIST: {item_list}")
        print("======================================================================")


# @Register
# class Bar:
#     def get_name():
#         return "bar"