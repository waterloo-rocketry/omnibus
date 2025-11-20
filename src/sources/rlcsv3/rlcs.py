import parsley
from parsley.fields import Enum, Numeric
import math

from omnibus.message_types import RLCSv3Message

Number = int | float

VALVE_COMMAND = {"CLOSED": 0, "OPEN": 1}
BOOLEAN = {"FALSE": 0, "TRUE": 1}
LIMIT_SWITCHES = {"UNKNOWN": 0, "OPEN": 1, "CLOSED": 2, "ERROR": 3}

MESSAGE_FORMAT = [
    Enum("OV101 Command", 8, VALVE_COMMAND),
    Enum("OV102 Command", 8, VALVE_COMMAND),
    Enum("OV301 Command", 8, VALVE_COMMAND),
    Enum("NV201 Command", 8, VALVE_COMMAND),
    Enum("CDV401 Command", 8, VALVE_COMMAND),
    Enum("QD301 Command", 8, VALVE_COMMAND),
    Enum("OV302 Command", 8, VALVE_COMMAND),

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
    Enum("CDV401 Lims", 8, LIMIT_SWITCHES),
    Enum("NV201 Lims", 8, LIMIT_SWITCHES),
    Numeric("Heater Thermistor Voltage 1", 16, big_endian=False),
    Numeric("Heater Thermistor Voltage 2", 16, big_endian=False),
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


def parse_rlcs(line: str | bytes) -> RLCSv3Message | None:
    '''parses data as well as checks for data validity
        returns none if data is invalid
    '''
    bit_str = parsley.BitString(data=line[1:-1])
    key_list_kelvin=["Heater Kelvin Low 1 Voltage","Heater Kelvin Low 2 Voltage"
                  "Heater Kelvin High 1 Voltage","Heater Kelvin High 2 Voltage"]
    try:
        res=parsley.parse_fields(bit_str, MESSAGE_FORMAT)
    except ValueError as e:
        print("Invalid data: " + str(e))
        return
    #Convert adc bits to voltage to allow for kelvin resistance calculation
    for key in ["Heater Thermistor Voltage 1","Heater Thermistor Voltage 2"]:
        res[key] = parse_adc_to_voltage(res[key], 10, 4.096)

    res["Heater Thermistor Temp 1"] = parse_thermistor(res["Heater Thermistor Voltage 1"])
    res["Heater Thermistor Temp 2"] = parse_thermistor(res["Heater Thermistor Voltage 2"])

    if res["Heater Current 1"] != 0:
        res["Heater Resistance 1"] = (res["Heater Kelvin High 1 Voltage"] - res["Heater Kelvin Low 1 Voltage"])/res["Heater Current 1"]
    else:
        res["Heater Resistance 1"] = 0.0

    if res["Heater Current 2"] != 0:
        res["Heater Resistance 2"] = (res["Heater Kelvin High 2 Voltage"] - res["Heater Kelvin Low 2 Voltage"])/res["Heater Current 2"]
    else:
        res["Heater Resistance 2"] = 0.0

    try:
        return RLCSv3Message(id=0, data=res, message_version=2)
    except Exception as e:
        print(f"Error creating Pydantic model: {e}")
        return None # Return None on failure to be consistent

def parse_thermistor(divider_vlt):
    # Second resistor in voltage divider
    VOLTAGE_DIVIDER_RES = 5000.0
    # resistance of the thermistor
    ST_RES = 10000.0
    # beta value of the thermistor
    BETA_VALUE = 3950.0
    # temperature of the thermistor resistance
    ST_TEMP_KEL = 298.15
    # input voltage to the thermistor voltage divider
    INPUT_VLT = 5.0

    if 0.0 < divider_vlt < INPUT_VLT:
        #resistance of the thermistor calculated using voltage divider
        thrmstr_rstnce = (VOLTAGE_DIVIDER_RES * INPUT_VLT / divider_vlt) - VOLTAGE_DIVIDER_RES
        # uses thermistor beta value to convert 
        # Formula: Beta=(ln(R1/R2))/((1/T1)-(1/T2))
        therm_temp_cel = ((math.log(thrmstr_rstnce / ST_RES) / BETA_VALUE) + 1.0 / ST_TEMP_KEL) ** -1 - 273.15
        return therm_temp_cel
    else:
        return 0.0

# resistance calculation is performed with voltages taken in from parsley
def parse_kelvin_resistance(voltageP,voltageN,current):
    if current != 0:
        return (voltageP - voltageN) / current 
    else:
        return 0.0

def parse_adc_to_voltage(adc_value,adc_bits, vref):
    return float(adc_value) / (2 ** adc_bits) * vref
