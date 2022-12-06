from calibration import Sensor, Connection, LinearCalibration, ThermistorCalibration

RATE = 1000  # Analog data sample rate
READ_BULK = 20  # Number of samples to read at once for better performance


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
       # Port 11
       Sensor("(PT-1) - Supply Cylinder Pressure", "ai7", 10, Connection.SINGLE,
              LinearCalibration(1/98.0*3000/0.016, -0.004*3000/0.016, "psi"))
       # Port 12
       Sensor("(PT-2) - Fill Line Pressure", "ai14", 10, Connection.SINGLE,
              LinearCalibration(1/98.0*3000/0.016, -0.004*3000/0.016, "psi"))
       # Port 1
       Sensor("Rocket Mass", "ai16", 0.2, Connection.DIFFERENTIAL,
              # Very estimated calibration 200 kG / (2.0 mV/V * 12V)
              LinearCalibration(39078, -46.1, "lbs"))
       # Port 2 - if used
       Sensor("Big Omega S-Type - Ox Tanks", "ai17", 0.2, Connection.DIFFERENTIAL,
              # Factory calibration: 1000 kG / (2.9991 mV/V * 12 V)
              LinearCalibration(1000 / (2.9991 / 1000 * 12), -10.1, "kg"))

       """
       Everything below here is just for documentation purposes
       """
       # For every V it powered it will output 2 mV when experiencing Maximum load.
       # Will output about 0 mV when experiencing nothing
       # Linear in between

       # Mass = m(volage * input power)
       # 200Kg = m (10 * 2 / 1000)
       # m = 200 / (10 * 2 / 1000)

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
