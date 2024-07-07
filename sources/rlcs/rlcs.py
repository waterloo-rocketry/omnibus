import parsley
from parsley.fields import Enum, Numeric

Number = int | float

VALVE_COMMAND = {"CLOSED": 0, "OPEN": 1}
BOOLEAN = {"FALSE": 0, "TRUE": 1}
LIMIT_SWITCHES = {"UNKNOWN": 0, "OPEN": 1, "CLOSED": 2, "ERROR": 3}

MESSAGE_FORMAT = [
    Enum("OV101 Command", 8, VALVE_COMMAND),
    Enum("OV102 Command", 8, VALVE_COMMAND),
    Enum("NV201 Command", 8, VALVE_COMMAND),
    Enum("NV202 Command", 8, VALVE_COMMAND),
    Enum("Vent Valve Command", 8, VALVE_COMMAND),
    Enum("Injector Valve Command", 8, VALVE_COMMAND),
    Enum("Fill Dump Valve Command", 8, VALVE_COMMAND),
    Enum("Fill Disconnect Command", 8, VALVE_COMMAND),
    Enum("Tank Heating 1 Command", 8, VALVE_COMMAND),
    Enum("Tank Heating 2 Command", 8, VALVE_COMMAND),
    Enum("Ignition Primary Command", 8, VALVE_COMMAND),
    Enum("Ignition Secondary Command", 8, VALVE_COMMAND),

    Numeric("Towerside Main Batt Voltage", 16, scale=1/1000, big_endian=False),
    Numeric("Towerside Actuator Batt Voltage", 16, scale=1/1000, big_endian=False),
    Numeric("Error Code", 16, big_endian=False),
    Enum("Towerside Armed", 8, BOOLEAN),
    Enum("Towerside Has Contact", 8, BOOLEAN),
    Numeric("Ignition Primary Current", 16, scale=1/1000, big_endian=False),
    Numeric("Ignition Secondary Current", 16, scale=1/1000, big_endian=False),
    Enum("OV101 Lims", 8, LIMIT_SWITCHES),
    Enum("OV102 Lims", 8, LIMIT_SWITCHES),
    Enum("NV201 Lims", 8, LIMIT_SWITCHES),
    Enum("NV202 Lims", 8, LIMIT_SWITCHES),
    #Enum("Fill Disconnect Lims", 8, LIMIT_SWITCHES),
    Numeric("Heater Thermistor 1", 16, scale=1/1000, big_endian=False),
    Numeric("Heater Thermistor 2", 16, scale=1/1000, big_endian=False),
    Numeric("Heater Current 1", 16, scale=1/1000, big_endian=False),
    Numeric("Heater Current 2", 16, scale=1/1000, big_endian=False),
    Numeric("Heater Battery 1 Voltage", 16, scale=1/1000, big_endian=False),
    Numeric("Heater Battery 2 Voltage", 16, scale=1/1000, big_endian=False),
    Numeric("Heater Kelvin Low 1 Voltage", 16, scale=1/1000, big_endian=False),
    Numeric("Heater Kelvin Low 2 Voltage", 16, scale=1/1000, big_endian=False),
    Numeric("Heater Kelvin High 1 Voltage", 16, scale=1/1000, big_endian=False),
    Numeric("Heater Kelvin High 2 Voltage", 16, scale=1/1000, big_endian=False),
]

EXPECTED_SIZE = 2 + parsley.calculate_msg_bit_len(MESSAGE_FORMAT) // 8

def print_data(parsed: dict[str, str | Number]):
    for k, v in parsed.items():
        print(f"{k}:\t{v}")


def parse_rlcs(line: str | bytes) -> dict[str, str | Number] | None:
    '''parses data as well as checks for data validity
        returns none if data is invalid
    '''
    bit_str = parsley.BitString(data=line[1:-1])
    try:
        return parsley.parse_fields(bit_str, MESSAGE_FORMAT)
    except ValueError as e:
        print("Invalid data: " + str(e))
        return None
