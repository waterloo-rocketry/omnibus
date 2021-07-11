from enum import Enum
import math

import nidaqmx

class Connection(Enum):
    SINGLE = nidaqmx.constants.TerminalConfiguration.RSE
    DIFFERENTIAL = nidaqmx.constants.TerminalConfiguration.DIFFERENTIAL

class Calibration:
    def __init__(self, unit):
        self.unit = unit

    def calibrate(self, value):
        return value

    def __repr__(self):
        return f"x ({self.unit})"

class LinearCalibration(Calibration):
    def __init__(self, slope, offset, unit):
        super().__init__(unit)
        self.slope = slope
        self.offset = offset

    def calibrate(self, value):
        return self.slope * value + self.offset

    def __repr__(self):
        return f"{self.slope}*x + {self.offset} ({self.unit})"

class ThermistorCalibration(Calibration):
    def __init__(self, resistance, B, r_inf):
        super().__init__("C")
        self.resistance = resistance
        self.B = B
        self.r_inf = r_inf

    def calibrate(self, value):
        R_therm = (value * self.resistance) / (5 - value)
        if R_therm <= 0:
            return 0
        return self.B / math.log(R_therm / self.r_inf) - 273.15

    def __repr__(self):
        return f"Thermistor({self.resistance}, {self.B}, x) ({self.unit})"

class Sensor:
    sensors = []
    """
    Represent a sensor plugged into the NI box
    """
    def __init__(self, name: str, channel: str, input_range: float,
                 connection: Connection,
                 calibration: Calibration):
        self.name = name
        self.channel = channel
        self.input_range = input_range
        self.connection = connection
        self.calibration = calibration
        Sensor.sensors.append(self)

    @staticmethod
    def setup(ai):
        for sensor in Sensor.sensors:
            ai.ai_channels.add_ai_voltage_chan(f"Dev1/{sensor.channel}",
                min_val=-sensor.input_range, max_val=sensor.input_range,
                terminal_config=sensor.connection.value)

    @staticmethod
    def print():
        print("Sensors:")
        for sensor in Sensor.sensors:
            print(f"  {sensor.name} on {sensor.channel} (max {sensor.calibration.calibrate(sensor.input_range):.0f} {sensor.calibration.unit})")

    def parse(data):
        res = {}
        for i, sensor in enumerate(Sensor.sensors):
            res[sensor.name] = [sensor.calibration.calibrate(d) for d in data[i]]
        return res
