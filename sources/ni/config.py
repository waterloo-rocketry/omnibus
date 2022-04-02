from calibration import Sensor, Connection, LinearCalibration, ThermistorCalibration

RATE = 1000  # Analog data sample rate
READ_BULK = 20  # Number of samples to read at once for better performance


def setup():
    Sensor("Honeywell S-Type - Fuel Tank Mass", "ai17", 0.2, Connection.DIFFERENTIAL,
            LinearCalibration(5116, -0.94, "kg")) # calibrated 13/3/2022
    Sensor("Omega S-Type - Ox Tank Mass", "ai18", 0.2, Connection.DIFFERENTIAL,
            LinearCalibration(3025.7, -1.37, "kg")) # calibrated 13/3/2022

    Sensor("PNew (PT-5) - Ox Injector", "ai5", 2, Connection.SINGLE,
            # Factory calibration mapping 4-20mA to 0-3000psi
            LinearCalibration(1/98.1*3000/0.016, -0.004*3000/0.016, "psi"))
    Sensor("P5 (PT-2) - Ox Fill", "ai19", 10, Connection.SINGLE,
            LinearCalibration(600, -54.9, "psi")) # calibrated 25/3/2022
    Sensor("P7 (PT-3) - Fuel Tank", "ai20", 10, Connection.SINGLE,
            LinearCalibration(600, -60.2, "psi")) # calibrated 25/3/2022
    Sensor("P9 - Ox tank PT2", "ai21", 10, Connection.SINGLE,
            LinearCalibration(601, -57.7, "psi")) # calibrated 26/3/2022
    #Sensor("SP1 (PT-1) - Ox Tank", "ai16", 0.2, Connection.DIFFERENTIAL,
    #        LinearCalibration(167706, -91.5, "psi")) # Calibrated 25/3/2022

    # Directly plugging in K-type thermocouples. 41uV / C and a cold junction temperature guessed at 23 C.
    Sensor("T1 - Ox Tank Temp A", "ai0", 0.2, Connection.DIFFERENTIAL,
            LinearCalibration(1 / (41 / 1000 / 1000), 0.0009 / (41 / 1000 / 1000), "C"))
    Sensor("T2 - Ox Tank Temp B", "ai1", 0.2, Connection.DIFFERENTIAL,
            LinearCalibration(1 / (41 / 1000 / 1000), 0.0009 / (41 / 1000 / 1000), "C"))
    Sensor("T3 - Fuel Tank Temp A", "ai3", 0.2, Connection.DIFFERENTIAL,
            LinearCalibration(1 / (41 / 1000 / 1000), 0.0009 / (41 / 1000 / 1000), "C"))
    Sensor("T4 - Fuel Tank Temp B", "ai4", 0.2, Connection.DIFFERENTIAL,
            LinearCalibration(1 / (41 / 1000 / 1000), 0.0009 / (41 / 1000 / 1000), "C"))

    #Sensor("Big Omega S-Type", "ai18", 0.2, Connection.DIFFERENTIAL,
    #        # Factory calibration: 1000 kG / (2.9991 mV/V * 10 V)
    #        LinearCalibration(1000 / (2.9991 / 1000 * 10), -10.1, "kg"))
    #Sensor("Thrust", "ai2", 0.2, Connection.DIFFERENTIAL, LinearCalibration(
    #    65445, -20.9, "lbs"))  # Roughly calibrated 17/7/2021
    Sensor("Pneumatic Pressure", "ai2", 10, Connection.SINGLE, LinearCalibration(
        35.3, -34.2, "psi"))  # Calibrated 13/7/2021
    #Sensor("T8 - Tank Heating", "ai23", 10, Connection.SINGLE,
    #       ThermistorCalibration(10000, 3434, 0.099524))  # Calibration pulled from LabVIEW
