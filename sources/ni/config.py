from calibration import Sensor, LinearCalibration, ThermistorCalibration, Connection

RATE = 10000  # Analog data sample rate
READ_BULK = 200  # Number of samples to read at once for better performance


CC = False

Sensor("Omega S-Type", "ai3", 0.2, Connection.DIFFERENTIAL, LinearCalibration(6637, -4.3, "lbs")) # Roughly calibrated 2/7/2021
# Sensor("Honeywell S-Type", "", 0.2, Connection.DIFFERENTIAL, LinearCalibration(18.3*61.2, -0.59*61.2, "lbs")) # RECALIBRATE
Sensor("P5 - Pneumatics", "ai7", 10, Connection.SINGLE, LinearCalibration(620, -39.1, "psi")) # Calibrated 2/7/2021
Sensor("P4 - Ox Fill", "ai6", 10, Connection.SINGLE, LinearCalibration(615, -44.1, "psi")) # Calibrated 2/7/2021
Sensor("P3 - Ox Tank", "ai0", 10, Connection.SINGLE, LinearCalibration(605, -53.3, "psi")) # Calibrated 2/7/2021
Sensor("T8 - Tank Heating", "ai23", 10, Connection.SINGLE, ThermistorCalibration(10000, 3434, 0.099524))
Sensor("SP1 - Nozzle", "ai5", 0.2, Connection.DIFFERENTIAL, LinearCalibration(5000, 0, "psi")) # RECALIBRATE

if CC:
    Sensor("P2 - CC", "ai4", 10, Connection.SINGLE, LinearCalibration(594.86, -231.2, "psi")) # Could use a calibration
    Sensor("Thrust", "ai2", 0.2, Connection.DIFFERENTIAL, LinearCalibration(98.07*328.2, -30.56*328.2, "lbs")) # RECALIBRATE
    Sensor("SP1 - Nozzle", "ai5", 0.2, Connection.DIFFERENTIAL, LinearCalibration(278.76*61.2, -17.42*61.2, "psi")) # RECALIBRATE
    Sensor("FAST", "ai1", 10, Connection.SINGLE, LinearCalibration(1, 0, "psi"))                       # CALIBRATE
    Sensor("T1 - CC", "ai16", 10, Connection.SINGLE, ThermistorCalibration(10000, 3434, 0.099524))
    Sensor("T2 - CC", "ai17", 10, Connection.SINGLE, ThermistorCalibration(10000, 3434, 0.099524))
    Sensor("T3 - CC", "ai18", 10, Connection.SINGLE, ThermistorCalibration(10000, 3434, 0.099524))
    Sensor("T4 - CC", "ai19", 10, Connection.SINGLE, ThermistorCalibration(10000, 3434, 0.099524))
    Sensor("T5 - CC", "ai20", 10, Connection.SINGLE, ThermistorCalibration(10000, 3434, 0.099524))
    Sensor("T6 - CC", "ai21", 10, Connection.SINGLE, ThermistorCalibration(10000, 3434, 0.099524))
    Sensor("T7 - CC", "ai22", 10, Connection.SINGLE, ThermistorCalibration(10000, 3434, 0.099524))
