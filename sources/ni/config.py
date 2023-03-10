from calibration import Sensor, Connection, LinearCalibration, ThermistorCalibration

RATE = 1000  # Analog data sample rate
READ_BULK = 20  # Number of samples to read at once for better performance

# Mapping between briefcase ports and ai channels such that you can do ports[1] through ports[12]
ports = [
    None,  # port 0
    "ai16", "ai17", "ai18",  # Differental channels 1-3
    "ai19", "ai27", "ai20",  # Direct voltage channels 4-6
    "ai28", "ai21", "ai29",  # 4-20 mA channels 7-9
    "ai15", "ai7",  "ai14",  # 4-20 mA channels 10-12
]

thermo_ports = [
    None,  # port 0
    "ai10", "ai2", "ai9", "ai1",  # Ports 1-4
    "ai8", "ai0"                  # Ports 5-6
]


def setup():
    """
    Test Values
    """
    Sensor("Power in", "ai31", 10, Connection.SINGLE,
           LinearCalibration(3, 0, "V"))
    Sensor("+12V", "ai23", 10, Connection.SINGLE,
           LinearCalibration(3, 0, "V"))
    Sensor("+10V", "ai30", 10, Connection.SINGLE,
           LinearCalibration(3, 0, "V"))
    Sensor("+5V", "ai22", 10, Connection.SINGLE,
           LinearCalibration(3, 0, "V"))

    """
    Sensor Configs, will change from test to test
    """
    
    # Standard TDL35 and TDM51 transducers: 4-20mA 0-3000 psi
    Sensor("PT-1 Ox Fill", ports[7], 10, Connection.SINGLE,
           LinearCalibration(1/98.0*3000/0.016, -0.004*3000/0.016, "psi"))
    Sensor("PT-2 Ox Tank", ports[8], 10, Connection.SINGLE,
           LinearCalibration(1/98.0*3000/0.016, -0.004*3000/0.016, "psi"))
    Sensor("PT-3 Fuel Tank", ports[9], 10, Connection.SINGLE,
           LinearCalibration(1/98.0*3000/0.016, -0.004*3000/0.016, "psi"))
    Sensor("PT-5 Ox Injector", ports[10], 10, Connection.SINGLE,
           LinearCalibration(1/98.0*3000/0.016, -0.004*3000/0.016, "psi"))
    Sensor("PT-6 CC 1", ports[11], 10, Connection.SINGLE,
           LinearCalibration(1/98.0*3000/0.016, -0.004*3000/0.016, "psi"))
    Sensor("PT-7 CC 2", ports[12], 10, Connection.SINGLE,
           LinearCalibration(1/98.0*3000/0.016, -0.004*3000/0.016, "psi"))
           
    # PSE540-R06 pneumatic transducer. 1-5V output for 0-1 MPa
    Sensor("PT-4 Pneumatics", ports[4], 10, Connection.SINGLE,
           LinearCalibration(145 / (5 - 1), -145 / (5 - 1), "psi"))

    # Perseus, 1500 psi with a FSO@10V of 75 mV, but we're running it at 12V.
    # Sensor("PT-5 Perseus", ports[3], 0.2, Connection.DIFFERENTIAL,
    #        LinearCalibration(1500 / (0.075 / 10 * 12), 0, "psi"))

    # Honeywell S-type, 1000 N (divide by 9.81 to kg) an 2.002 mv/V at 12V
    Sensor("Honeywell S-type - Ox Tank", ports[1], 0.2, Connection.DIFFERENTIAL,
           LinearCalibration((1000/9.81)/(2.002/1000*12), -0.7, "kg"))
    
    # Omega S-type (LC-103B), 200 lb (divide by 2.2 to kg), 3 mV/V at 12V
    Sensor("Omega S-Type - Fuel Tank", ports[2], 0.2, Connection.DIFFERENTIAL,
           LinearCalibration((200/2.205) / (3/1000*12), -1.9, "kg"))

    # Omega LC501 2000 lbf (divide by 2.2 to kg), 3 mv/v, 12v excitation
    Sensor("Thrust", ports[3], 0.2, Connection.DIFFERENTIAL,
           LinearCalibration((2000/2.205) / (3/1000*12), -7.4, "kg"))

    # CAS BSA-5KLB 5000 lbf (divide by 2.2 to kg), 3 mv/v, 12v excitation
    # Sensor("Thrust", ports[3], 0.2, Connection.DIFFERENTIAL,
    #        LinearCalibration((5000/2.205) / (3/1000*12), -20, "kg"))

    # Vent Thermistor with a 10k resistor divider between it and ground
    # Sensor("Vent Thermistor", ports[12], 10, Connection.SINGLE,
    #        ThermistorCalibration(12, 10000, 3434, 0.099524))  # Calibration pulled from LabVIEW

    # Thermocouples using Spidey Sense R3 and 0-5V converter boards
    Sensor("Thermocouple 1", thermo_ports[1], 5, Connection.SINGLE,
           LinearCalibration(1200/5, -100 + (23.4 - -18), "C"))
    Sensor("Thermocouple 2", thermo_ports[2], 5, Connection.SINGLE,
           LinearCalibration(1200/5, -100 + (23.4 - -3), "C"))
    Sensor("Thermocouple 3", thermo_ports[3], 5, Connection.SINGLE,
           LinearCalibration(1200/5, -100 + (23.4 - -24), "C"))
    Sensor("Thermocouple 4", thermo_ports[4], 5, Connection.SINGLE,
           LinearCalibration(1200/5, -100, "C"))
    
    # Thermocouples using the blue 4-20mA converters.
    Sensor("Thermocouple 5", thermo_ports[5], 5, Connection.SINGLE,
           LinearCalibration(1/220*1300/0.016, -0.004*1300/0.016, "C"))
    Sensor("Thermocouple 6", thermo_ports[6], 5, Connection.SINGLE,
           LinearCalibration(1/220*1300/0.016, -0.004*1300/0.016, "C"))

    """
    Everything below here is just for documentation purposes
    """
    # Sensor("Honeywell S-Type - Fuel Tank Mass", "ai17", 0.2, Connection.DIFFERENTIAL,
    #        LinearCalibration(5116, -0.94, "kg"))  # calibrated 13/3/2022

    # Sensor("PNew (PT-5) - Ox Injector", "ai5", 2, Connection.SINGLE,
    #     # Factory calibration mapping 4-20mA to 0-3000psi
    #        LinearCalibration(1/98.1*3000/0.016, -0.004*3000/0.016, "psi"))
    # Sensor("P5 (PT-2) - Ox Tank", "ai19", 10, Connection.SINGLE,
    #        LinearCalibration(600, -54.9, "psi")) # calibrated 25/3/2022
    # Sensor("PNew3 (PT-3) - Fuel Tank", "ai7", 10, Connection.SINGLE,
    #        LinearCalibration(1/98.0*3000/0.016, -0.004*3000/0.016, "psi"))
    # Sensor("PNew2 - Fuel Injector", "ai6", 10, Connection.SINGLE,
    #        LinearCalibration(1/98.3*3000/0.016, -0.004*3000/0.016, "psi"))
    # Sensor("PNew4 - Ox Tanks", "ai2", 10, Connection.SINGLE,
    #        LinearCalibration(1/98.3*3000/0.016, -0.004*3000/0.016, "psi"))
    # Sensor("SP1 (PT-1) - Ox Fill", "ai16", 0.2, Connection.DIFFERENTIAL,
    #        LinearCalibration(167706, -91.5, "psi"))  # Calibrated 25/3/2022

    # # Directly plugging in K-type thermocouples. 41uV / C and a cold junction temperature guessed at 23 C.
    # Sensor("T1 - Ox Tank Temp A", "ai0", 0.2, Connection.DIFFERENTIAL,
    #        LinearCalibration(1 / (41 / 1000 / 1000), 0.0009 / (41 / 1000 / 1000), "C"))
    # Sensor("T2 - Ox Tank Temp B", "ai1", 0.2, Connection.DIFFERENTIAL,
    #        LinearCalibration(1 / (41 / 1000 / 1000), 0.0009 / (41 / 1000 / 1000), "C"))
    # Sensor("T3 - Fuel Tank Temp A", "ai3", 0.2, Connection.DIFFERENTIAL,
    #        LinearCalibration(1 / (41 / 1000 / 1000), 0.0009 / (41 / 1000 / 1000), "C"))
    # Sensor("T4 - Fuel Tank Temp B", "ai4", 0.2, Connection.DIFFERENTIAL,
    #        LinearCalibration(1 / (41 / 1000 / 1000), 0.0009 / (41 / 1000 / 1000), "C"))

    # Sensor("Big Omega S-Type", "ai17", 0.2, Connection.DIFFERENTIAL,
    #         # Factory calibration: 1000 kG / (2.9991 mV/V * 10 V)
    #         LinearCalibration(1000 / (2.9991 / 1000 * 10), -10.1, "kg"))
    # Sensor("Thrust", "ai2", 0.2, Connection.DIFFERENTIAL,
    #        LinearCalibration(65445, -20.9, "lbs"))  # Roughly calibrated 17/7/2021
    # Sensor("Pneumatic Pressure", "ai19", 10, Connection.SINGLE,
    #        LinearCalibration(35.3, -34.2, "psi"))  # Calibrated 13/7/2021
    # Sensor("T8 - Tank Heating", "ai23", 10, Connection.SINGLE,
    #        ThermistorCalibration(10000, 3434, 0.099524))  # Calibration pulled from LabVIEW
