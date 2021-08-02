from calibration import Sensor, Connection, LinearCalibration, ThermistorCalibration

RATE = 10000  # Analog data sample rate
READ_BULK = 200  # Number of samples to read at once for better performance

CC = True


def setup():
    Sensor("Omega S-Type", "ai3", 0.2, Connection.DIFFERENTIAL,
           LinearCalibration(6637, -4.3, "lbs"))  # Roughly calibrated 2/7/2021
    # Sensor("Honeywell S-Type", "", 0.2, Connection.DIFFERENTIAL, LinearCalibration(18.3*61.2, -0.59, "lbs")) # RECALIBRATE
    Sensor("P5 (PT-5) - SRAD Vent Valve", "ai7", 10, Connection.SINGLE,
           LinearCalibration(620, -39.1, "psi"))  # Calibrated 2/7/2021
    Sensor("P4 (PT-1) - Ox Fill", "ai6", 10, Connection.SINGLE,
           LinearCalibration(615, -44.1, "psi"))  # Calibrated 2/7/2021
    Sensor("P3 (PT-2) - Ox Tank", "ai0", 10, Connection.SINGLE,
           LinearCalibration(605, -53.3, "psi"))  # Calibrated 2/7/2021
    Sensor("T8 - Tank Heating", "ai23", 10, Connection.SINGLE,
           ThermistorCalibration(10000, 3434, 0.099524))  # Calibration pulled from LabVIEW

    if CC:
        Sensor("P2 (PT-3) - CC", "ai4", 10, Connection.SINGLE,
               LinearCalibration(621, -267, "psi"))  # Calibrated 13/7/2021
        Sensor("Thrust", "ai2", 0.2, Connection.DIFFERENTIAL, LinearCalibration(
            65445, -20.9, "lbs"))  # Roughly calibrated 17/7/2021
        Sensor("SP1 (PT-4) - Nozzle", "ai5", 0.2, Connection.DIFFERENTIAL,
               LinearCalibration(171346, -99.8, "psi"))  # Calibrated 2/7/2021
        Sensor("FAST", "ai1", 10, Connection.SINGLE, LinearCalibration(
            35.3, -34.2, "psi"))  # Calibrated 13/7/2021
        Sensor("T1 - CC", "ai16", 10, Connection.SINGLE,
               ThermistorCalibration(10000, 3434, 0.099524))  # Calibration pulled from LabVIEW
        Sensor("T2 - CC", "ai17", 10, Connection.SINGLE,
               ThermistorCalibration(10000, 3434, 0.099524))  # Calibration pulled from LabVIEW
        Sensor("T3 - CC", "ai18", 10, Connection.SINGLE,
               ThermistorCalibration(10000, 3434, 0.099524))  # Calibration pulled from LabVIEW
        Sensor("T4 - CC", "ai19", 10, Connection.SINGLE,
               ThermistorCalibration(10000, 3434, 0.099524))  # Calibration pulled from LabVIEW
        Sensor("T5 - CC", "ai20", 10, Connection.SINGLE,
               ThermistorCalibration(10000, 3434, 0.099524))  # Calibration pulled from LabVIEW
        Sensor("T6 - CC", "ai21", 10, Connection.SINGLE,
               ThermistorCalibration(10000, 3434, 0.099524))  # Calibration pulled from LabVIEW
        Sensor("T7 - CC", "ai22", 10, Connection.SINGLE,
               ThermistorCalibration(10000, 3434, 0.099524))  # Calibration pulled from LabVIEW
