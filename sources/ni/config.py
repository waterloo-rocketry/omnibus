from calibration import Sensor, Connection, LinearCalibration, ThermistorCalibration

RATE = 1000  # Analog data sample rate
READ_BULK = 20  # Number of samples to read at once for better performance


def setup():
    Sensor("Power in", "ai31", 10, Connection.SINGLE,
           LinearCalibration(3, 0, "V"))
    Sensor("+12V", "ai23", 10, Connection.SINGLE,
           LinearCalibration(3, 0, "V"))
    Sensor("+10V", "ai30", 10, Connection.SINGLE,
           LinearCalibration(3, 0, "V"))
    Sensor("+5V", "ai22", 10, Connection.SINGLE,
           LinearCalibration(3, 0, "V"))

    Sensor("Omega S-Type - Ox Tank Mass", "ai17", 0.2, Connection.DIFFERENTIAL,
            LinearCalibration(3025.7, -1.37, "kg")) # calibrated 13/3/2022
    #Sensor("Big Omega S-Type - Ox Tanks", "ai18", 0.2, Connection.DIFFERENTIAL,
    #       # Factory calibration: 1000 kG / (2.9991 mV/V * 10 V)
    #       LinearCalibration(1000 / (2.9991 / 1000 * 10), -10.1, "kg"))
    #Sensor("Honeywell S-Type - Fuel Tank Mass", "ai17", 0.2, Connection.DIFFERENTIAL,
    #       LinearCalibration(5116, -0.94, "kg"))  # calibrated 13/3/2022
    Sensor("Thrust", "ai16", 0.2, Connection.DIFFERENTIAL, LinearCalibration(
            # Factory Calibration: 2000 lbs / (3.002 mV/V * 12 V)
            2000 / (3.002 / 1000 * 12), -11, "lbs"))
            #65445, -20.9, "lbs"))  # Roughly calibrated 17/7/2021

    Sensor("PT-1 Ox Fill", "ai15", 2, Connection.SINGLE,
           # Factory calibration mapping 4-20mA to 0-3000psi
           LinearCalibration(1/98.1*3000/0.016, -0.004*3000/0.016 +10, "psi"))
    Sensor("PT-2 Ox Tank", "ai7", 2, Connection.SINGLE,
           # Factory calibration mapping 4-20mA to 0-3000psi
           LinearCalibration(1/98.1*3000/0.016, -0.004*3000/0.016 +10, "psi"))
    Sensor("PT-3 CC", "ai14", 2, Connection.SINGLE,
           # Factory calibration mapping 4-20mA to 0-3000psi
           LinearCalibration(1/98.1*3000/0.016, -0.004*3000/0.016 +10, "psi"))
    #Sensor("SP1 (PT-1) - Ox Fill", "ai16", 0.2, Connection.DIFFERENTIAL,
    #       LinearCalibration(167706, -91.5, "psi"))  # Calibrated 25/3/2022
    # Sensor("P5 (PT-2) - Ox Tank", "ai19", 10, Connection.SINGLE,
    #        LinearCalibration(600, -54.9, "psi")) # calibrated 25/3/2022
    #Sensor("Old cylindrical pneumatic transducer", "ai19", 10, Connection.SINGLE, LinearCalibration(
    #    35.3, -34.2, "psi"))  # Calibrated 13/7/2021
    Sensor("PT-4 Pneumatics", "ai19", 10, Connection.SINGLE,
            # Factory calibration mapping 1-5V to 0 - 145 psi
            LinearCalibration(145 / 4, - 145/4, "psi"))

    # Directly K-type thermocouples with amplification of 18.1. 41uV / C
    Sensor("T1", "ai0", 2, Connection.SINGLE,
        LinearCalibration(1/(41*18.1/1000000), 0, "C"))
    Sensor("T2", "ai8", 2, Connection.SINGLE,
        LinearCalibration(1/(41*18.1/1000000), 0, "C"))
    Sensor("T3", "ai1", 2, Connection.SINGLE,
        LinearCalibration(1/(41*18.1/1000000), 0, "C"))
    Sensor("T4", "ai9", 2, Connection.SINGLE,
        LinearCalibration(1/(41*18.1/1000000), 0, "C"))

    Sensor("Tank Heating", "ai29", 10, Connection.SINGLE,
           ThermistorCalibration(5, 10200, 3434, 0.099524))  # Calibration pulled from LabVIEW
    Sensor("Vent Thermistor", "ai21", 10, Connection.SINGLE,
           ThermistorCalibration(5, 10200, 3434, 0.099524))  # Calibration pulled from LabVIEW
