import math
from typing import cast

import parsley  # pyright: ignore[reportMissingTypeStubs]
from parsley.fields import Enum, Field, Numeric  # pyright: ignore[reportMissingTypeStubs]

Number = int | float

VALVE_COMMAND: dict[str, int] = {"CLOSED": 0, "OPEN": 1}
BOOLEAN: dict[str, int] = {"FALSE": 0, "TRUE": 1}
LIMIT_SWITCHES: dict[str, int] = {"UNKNOWN": 0, "OPEN": 1, "CLOSED": 2, "ERROR": 3}

MESSAGE_FORMAT: list[Field] = [
    Enum("OV101 Command", 8, VALVE_COMMAND),
    Enum("OV102 Command", 8, VALVE_COMMAND),
    Enum("OV103 Command", 8, VALVE_COMMAND),
    Enum("NV201 Command", 8, VALVE_COMMAND),
    Enum("CDV401 Command", 8, VALVE_COMMAND),
    Enum("QD301 Command", 8, VALVE_COMMAND),
    Enum("OV302 Command", 8, VALVE_COMMAND),
    Enum("Pyro Valve Command", 8, VALVE_COMMAND),

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

def print_data(parsed: dict[str, str | Number]) -> None:
    for k, v in parsed.items():
        print(f"{k}:\t{v}")


def parse_rlcs(line: str | bytes) -> dict[str, str | Number] | None:
    '''parses data as well as checks for data validity
        returns none if data is invalid
    '''
    data = line.encode() if isinstance(line, str) else line
    bit_str = parsley.BitString(data=data[1:-1])  # pyright: ignore[reportMissingTypeStubs]
    key_list_kelvin = ["Heater Kelvin Low 1 Voltage", "Heater Kelvin Low 2 Voltage", "Heater Kelvin High 1 Voltage", "Heater Kelvin High 2 Voltage"]
    try:
        res = parsley.parse_fields(bit_str, MESSAGE_FORMAT)  # pyright: ignore[reportMissingTypeStubs]
    except ValueError as e:
        print("Invalid data: " + str(e))
        return None
    # Convert adc bits to voltage to allow for kelvin resistance calculation
    for key in ["Heater Thermistor Voltage 1", "Heater Thermistor Voltage 2"]:
        if key in res:
            res[key] = parse_adc_to_voltage(cast(Number, res[key]), 10, 4.096)
    for index, key in enumerate(["Heater Resistance 1", "Heater Resistance 2"]):
        if key in res and 2 + index < len(key_list_kelvin):
            res[key] = parse_kelvin_resistance(
                cast(Number, res[key]),
                cast(Number, res[key_list_kelvin[2 + index]]),
                cast(Number, res[key_list_kelvin[index]]),
            )

    if "Heater Thermistor Voltage 1" in res:
        res.update({"Heater Thermistor Temp 1": parse_thermistor(cast(Number, res["Heater Thermistor Voltage 1"]))})
    if "Heater Thermistor Voltage 2" in res:
        res.update({"Heater Thermistor Temp 2": parse_thermistor(cast(Number, res["Heater Thermistor Voltage 2"]))})

    if cast(Number, res["Heater Current 1"]) != 0:
        res.update(
            {
                "Heater Resistance 1": (
                    cast(Number, res["Heater Kelvin High 1 Voltage"])
                    - cast(Number, res["Heater Kelvin Low 1 Voltage"])
                )
                / cast(Number, res["Heater Current 1"])
            }
        )
    else:
        res.update({"Heater Resistance 1": 0.0})

    if cast(Number, res["Heater Current 2"]) != 0:
        res.update(
            {
                "Heater Resistance 2": (
                    cast(Number, res["Heater Kelvin High 2 Voltage"])
                    - cast(Number, res["Heater Kelvin Low 2 Voltage"])
                )
                / cast(Number, res["Heater Current 2"])
            }
        )
    else:
        res.update({"Heater Resistance 2": 0.0})

    return res
        
 
    
def parse_thermistor(divider_vlt: Number) -> float:
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
        # resistance of the thermistor calculated using voltage divider
        thrmstr_rstnce = (VOLTAGE_DIVIDER_RES * INPUT_VLT / divider_vlt) - VOLTAGE_DIVIDER_RES
        # uses thermistor beta value to convert
        # Formula: Beta=(ln(R1/R2))/((1/T1)-(1/T2))
        therm_temp_cel = ((math.log(thrmstr_rstnce / ST_RES) / BETA_VALUE) + 1.0 / ST_TEMP_KEL) ** -1 - 273.15
        return float(therm_temp_cel)
    else:
        return 0.0

# resistance calculation is performed with voltages taken in from parsley
def parse_kelvin_resistance(voltageP: Number, voltageN: Number, current: Number) -> float:
    if current != 0:
        return float((voltageP - voltageN) / current)
    else:
        return 0.0


def parse_adc_to_voltage(adc_value: Number, adc_bits: int, vref: Number) -> float:
    return float(adc_value) / (2 ** adc_bits) * float(vref)
