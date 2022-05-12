from enum import Enum
import math

import nidaqmx


class Connection(Enum):
    """
    Represents how a sensor is wired into the NI box.
    """
    SINGLE = nidaqmx.constants.TerminalConfiguration.RSE  # ground referenced single ended
    DIFFERENTIAL = nidaqmx.constants.TerminalConfiguration.BAL_DIFF


class Calibration:
    """
    Represents a calibration curve which transforms a voltage input into a value
    with units.
    """

    def __init__(self, unit):
        self.unit = unit

    def calibrate(self, value):
        """
        Apply the calibration to an input voltage.
        """
        return value

    def __repr__(self):
        return f"x ({self.unit})"


class LinearCalibration(Calibration):
    """
    Represents a linear calibration with a configurable slope and zero offset.
    """

    def __init__(self, slope, offset, unit):
        super().__init__(unit)
        self.slope = slope
        self.offset = offset

    def calibrate(self, value):
        return self.slope * value + self.offset

    def __repr__(self):
        return f"{self.slope}*x + {self.offset} ({self.unit})"


class ThermistorCalibration(Calibration):
    """
    Represents the calibration for a thermistor.
    """

    def __init__(self, voltage, resistance, B, r_inf):
        super().__init__("C")
        self.voltage = voltage # voltage powering the thermistor
        self.resistance = resistance  # voltage divider resistance
        self.B = B  # not sure, pulled from the LabVIEW
        self.r_inf = r_inf  # not sure, pulled from the LabVIEW

    def calibrate(self, value):
        # thermistor magic pulled from the LabVIEW
        R_therm = (value * self.resistance) / (self.voltage - value)
        if R_therm <= 0:
            return 0
        return self.B / math.log(R_therm / self.r_inf) - 273.15

    def __repr__(self):
        return f"Thermistor({self.voltage}, {self.resistance}, {self.B}, x) ({self.unit})"


class Sensor:
    sensors = []
    """
    Represents a sensor plugged into the NI box. Instantiating members of this
    class sets up the sensors used with the static methods.
    """

    def __init__(self, name: str, channel: str, input_range: float,
                 connection: Connection,
                 calibration: Calibration):
        self.name = name
        self.channel = channel  # NI box channel, eg ai8
        self.input_range = input_range  # Voltage range for the NI box. 10, 5, 1 or 0.2.
        self.connection = connection  # single or differential
        self.calibration = calibration
        for sensor in Sensor.sensors:
            if sensor.name == self.name:
                raise KeyError(f"Duplicate sensors named {self.name}")

        Sensor.sensors.append(self)

    @staticmethod
    def setup(ai):
        """
        Set up the NI analog input task with the initialized sensors.
        """
        for sensor in Sensor.sensors:
            ai.ai_channels.add_ai_voltage_chan(f"Dev1/{sensor.channel}",
                                               min_val=-sensor.input_range, max_val=sensor.input_range,
                                               terminal_config=sensor.connection.value)

    @staticmethod
    def print():
        """
        Pretty print the initialized sensors.
        """
        print("Sensors:")
        for sensor in Sensor.sensors:
            print(f"  {sensor.name} ({sensor.calibration.unit}) on {sensor.channel}")

    @staticmethod
    def parse(data):
        """
        Apply each sensor's calibration to voltages from the NI box.
        """
        res = {}
        for i, sensor in enumerate(Sensor.sensors):
            res[sensor.name] = [sensor.calibration.calibrate(d) for d in data[i]]
        return res
