import parsley

VALVE_COMMAND = {"CLOSED": 0, "OPEN": 1}
BOOLEAN = {"FALSE": 0, "TRUE": 1}
LIMIT_SWITCHES = {"UNKNOWN": 0, "OPEN": 1, "CLOSED": 2, "ERROR": 3}

MESSAGE_FORMAT = [
    parsley.fields.Enum("VA1 Command", 8, VALVE_COMMAND),
    parsley.fields.Enum("VA2 Command", 8, VALVE_COMMAND),
    parsley.fields.Enum("VA3 Command", 8, VALVE_COMMAND),
    parsley.fields.Enum("VA4 Command", 8, VALVE_COMMAND),
    parsley.fields.Enum("Ignition Primary Command", 8, VALVE_COMMAND),
    parsley.fields.Enum("Ignition Secondary Command", 8, VALVE_COMMAND),
    parsley.fields.Enum("Rocket Power Command", 8, VALVE_COMMAND),
    parsley.fields.Enum("Fill Disconnect Command", 8, VALVE_COMMAND),
    parsley.fields.Numeric("Towerside Main Batt", 16, scale=1/1000, big_endian=False),
    parsley.fields.Numeric("Towerside Actuator Batt", 16, scale=1/1000, big_endian=False),
    parsley.fields.Numeric("Error Code", 16, big_endian=False),
    parsley.fields.Enum("Towerside Armed", 8, BOOLEAN),
    parsley.fields.Enum("Towerside Has Contact", 8, BOOLEAN),
    parsley.fields.Numeric("Ignition Primary Current", 16, scale=1/1000, big_endian=False),
    parsley.fields.Numeric("Ignition Secondary Current", 16, scale=1/1000, big_endian=False),
    parsley.fields.Enum("VA1 Lims", 8, LIMIT_SWITCHES),
    parsley.fields.Enum("VA2 Lims", 8, LIMIT_SWITCHES),
    parsley.fields.Enum("VA3 Lims", 8, LIMIT_SWITCHES),
    parsley.fields.Enum("VA4 Lims", 8, LIMIT_SWITCHES),
    parsley.fields.Enum("Fill Disconnect Lims", 8, LIMIT_SWITCHES),
]

def print_data(parsed):
    for k, v in parsed.items():
        print(f"{k}:\t{v}")

def parse_rlcs(line):
    '''parses data as well as checks for data validity 
        returns none if data is invalid 
    '''
    if not check_data_is_valid(line):
        return None

    bit_str = parsley.BitString(data=line[1:-1])
    try:
        return parsley.parse_fields(bit_str, MESSAGE_FORMAT)
    except ValueError as e:
        print("Invalid data: " + str(e))
        return None


def check_data_is_valid(line):
    '''
    Checks whether or not line is valid RLCS data. 
    If it is, returns True. If not, returns False.
    A valid line looks like W[xxxx]R where xxxx are data bytes.
    The line must also begin with W and end with R. 
    '''

    expected_size = 2 + parsley.calculate_msg_bit_len(MESSAGE_FORMAT) // 8
    if len(line) != expected_size:
        print("Warning: Format of data {} is wrong. Expected {} characters, got {}".format(
            line, expected_size, len(line)))
        return False
        # In the future, we may want to extract information from the message despite poor formatting

    if line[0] != ord('W') or line[-1] != ord('R'):
        print("Warning: Data {} is invalid (must end with R and begin with W)".format(line))
        return False

    return True
