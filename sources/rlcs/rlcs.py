import parsley
from parsley.fields import Enum, Numeric
import math

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
    Numeric("Heater Resistance 1", 16, scale=1,big_endian=False),#new field declaration to send these fields over omnibus
    Numeric("Heater Resistance 2", 16, scale=1,big_endian=False),#new field declaration to send these fields over omnibus
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
    key_list_kelvin=["Heater Kelvin Low 1 Voltage","Heater Kelvin Low 2 Voltage"
                  "Heater Kelvin High 1 Voltage","Heater Kelvin High 2 Voltage"]
    try:
        res=parsley.parse_fields(bit_str, MESSAGE_FORMAT)
    except ValueError as e:
        print("Invalid data: " + str(e))
        return 
    
    for key in ["Heater Current 1","Heater Current 2"]:
        res[key] = parse_thermistor(res[key],10,4.096)

    #Convert adc bits to voltage to allow for kelvin resistance calculation
    for key in ["Heater Kelvin Low 1 Voltage","Heater Kelvin Low 2 Voltage"
                  "Heater Kelvin High 1 Voltage","Heater Kelvin High 2 Voltage"]:
        res[key] = parse_adc_to_voltage(res[key],10,4.096)

    for index, key in enumerate(["Heater Resistance 1","Heater Resistance 2"]):
        res[key] = parse_kelvin_resistance(res[key],key_list_kelvin[2+index],key_list_kelvin[index])

    return res
        
 
    
def parse_thermistor(adc_value, adc_bits,vref):
    #Second resistor in voltage divider
    vlt_dvdr_rstr=5000.0
    #resistance of the thermistor
    st_rstnce=10000.0
    #beta value of the thermistor
    beta_value=3950.0
    #temperature of the thermistor resistance
    st_tmp_cel=25.0
    #input voltage to the thermistor voltage divider
    inpt_vlt=5.0

    #convert the adc output to voltage output
    thrmstr_vlt= parse_adc_to_voltage(adc_value,adc_bits,vref)

    #resistance of the thermistor calculated using voltage divider
    thrmstr_rstnce=vlt_dvdr_rstr * inpt_vlt / thrmstr_vlt - vlt_dvdr_rstr
    
    #uses thermistor beta value to convert 
    # Formula: Beta=(ln(R1/R2))/((1/T1)-(1/T2))
    therm_temp_cel = ((math.log (thrmstr_rstnce / st_rstnce) / beta_value)+ 1.0 / st_tmp_cel)**-1
    return therm_temp_cel

# resistance calculation is performed with voltages taken in from parsley
def parse_kelvin_resistance(voltageP,voltageN,current):
    try:
        return (voltageP - voltageN) / current 
    except ZeroDivisionError as e:
        return 0.0


def parse_adc_to_voltage(adc_value,adc_bits, vref):
    return float(adc_value) / (2**adc_bits) * vref
