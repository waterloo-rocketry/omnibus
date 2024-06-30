import parsley
from parsley.fields import Enum, Number, Numeric

VALVE_COMMAND = {"CLOSED": 0, "OPEN": 1}
BOOLEAN = {"FALSE": 0, "TRUE": 1}
LIMIT_SWITCHES = {"UNKNOWN": 0, "OPEN": 1, "CLOSED": 2, "ERROR": 3}

MESSAGE_FORMAT = [
    Enum("VA1 Command", 8, VALVE_COMMAND),
    Enum("VA2 Command", 8, VALVE_COMMAND),
    Enum("VA3 Command", 8, VALVE_COMMAND),
    Enum("VA4 Command", 8, VALVE_COMMAND),
    Enum("Vent Valve Command", 8, VALVE_COMMAND),
    Enum("Injector Valve Command", 8, VALVE_COMMAND),
    Enum("Ignition Primary Command", 8, VALVE_COMMAND),
    Enum("Ignition Secondary Command", 8, VALVE_COMMAND),
    Enum("Rocket Power Command", 8, VALVE_COMMAND),
    Enum("Fill Disconnect Command", 8, VALVE_COMMAND),
    Numeric("Towerside Main Batt", 16, scale=1/1000, big_endian=False),
    Numeric("Towerside Actuator Batt", 16, scale=1/1000, big_endian=False),
    Numeric("Error Code", 16, big_endian=False),
    Enum("Towerside Armed", 8, BOOLEAN),
    Enum("Towerside Has Contact", 8, BOOLEAN),
    Numeric("Ignition Primary Current", 16, scale=1/1000, big_endian=False),
    Numeric("Ignition Secondary Current", 16, scale=1/1000, big_endian=False),
    Enum("VA1 Lims", 8, LIMIT_SWITCHES),
    Enum("VA2 Lims", 8, LIMIT_SWITCHES),
    Enum("VA3 Lims", 8, LIMIT_SWITCHES),
    Enum("VA4 Lims", 8, LIMIT_SWITCHES),
    Enum("Fill Disconnect Lims", 8, LIMIT_SWITCHES),
    Numeric("Heater Thermistor 1", 16,scale=1/1000, big_endian=False),
    Numeric("Heater Thermistor 2", 16,scale=1/1000, big_endian=False),
    Numeric("Heater Current 1",16,scale=1/1000,big_endian=False),
    Numeric("Heater Current 2",16,scale=1/1000,big_endian=False),
    Numeric("Heater Battery 1", 16,scale=1/1000, big_endian=False),
    Numeric("Heater Battery 2", 16,scale=1/1000, big_endian=False),
    Numeric("Heater Kelvin Low 1", 16,scale=1/1000, big_endian=False),
    Numeric("Heater Kelvin Low 2", 16,scale=1/1000, big_endian=False),
    Numeric("Heater Kelvin High 1", 16,scale=1/1000, big_endian=False),
    Numeric("Heater Kelvin High 2", 16,scale=1/1000, big_endian=False),
]


def print_data(parsed: dict[str, str | Number]):
    for k, v in parsed.items():
        print(f"{k}:\t{v}")


def parse_rlcs(line: str | bytes) -> dict[str, str | Number] | None:
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


def check_data_is_valid(line: str | bytes) -> bool:
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
