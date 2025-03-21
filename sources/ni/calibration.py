from enum import Enum
import math

import nidaqmx

from typing import ClassVar, Self

class Connection(Enum):
    """
    Represents how a sensor is wired into the NI box.
    """
    # ground referenced single ended
    SINGLE = nidaqmx.constants.TerminalConfiguration.RSE  # pyright: ignore[reportAttributeAccessIssue]
    DIFFERENTIAL = nidaqmx.constants.TerminalConfiguration.DIFF # pyright: ignore[reportAttributeAccessIssue]


class Calibration:
    """
    Represents a calibration curve which transforms a voltage input into a value
    with units.
    """

    def __init__(self, unit: str):
        self.unit = unit

    def calibrate(self, value: float | int) -> float | int:
        """
        Apply the calibration to an input voltage.
        """
        return value

    def __repr__(self) -> str:
        return f"x ({self.unit})"


class LinearCalibration(Calibration):
    """
    Represents a linear calibration with a configurable slope and zero offset.
    """

    def __init__(self, slope: float | int, offset: float | int, unit: str):
        super().__init__(unit)
        self.slope = slope
        self.offset = offset

    def calibrate(self, value: float | int) -> float | int:
        return self.slope * value + self.offset

    def __repr__(self) -> str:
        return f"{self.slope}*x + {self.offset} ({self.unit})"


class ThermistorCalibration(Calibration):
    """
    Represents the calibration for a thermistor.
    """

    def __init__(self, voltage: float | int, resistance: float | int, B: float | int, r_inf: float | int):
        super().__init__("C")
        self.voltage = voltage  # voltage powering the thermistor
        self.resistance = resistance  # voltage divider resistance
        self.B = B  # not sure, pulled from the LabVIEW
        self.r_inf = r_inf  # not sure, pulled from the LabVIEW

    def calibrate(self, value: float | int) -> float | int:
        # thermistor magic pulled from the LabVIEW
        R_therm = (self.voltage - value) / (value / self.resistance)
        if R_therm <= 0:
            return 0
        return self.B / math.log(R_therm / self.r_inf) - 273.15

    def __repr__(self) -> str:
        return f"Thermistor({self.voltage}, {self.resistance}, {self.B}, x) ({self.unit})"


class Sensor:

    sensors: ClassVar[list[Self]] = []

    """
    Represents a sensor plugged into the NI box. Instantiating members of this
    class sets up the sensors used with the static methods.
    """

    def __init__(self, name: str, channel: str, input_range: float | int,
                 connection: Connection,
                 calibration: Calibration) -> None:
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
    def setup(ai: nidaqmx.Task) -> None:
        """
        Set up the NI analog input task with the initialized sensors.
        """
        for sensor in Sensor.sensors:
            ai.ai_channels.add_ai_voltage_chan(f"Dev1/{sensor.channel}",
                                               min_val=-sensor.input_range, max_val=sensor.input_range,
                                               terminal_config=sensor.connection.value)

    @staticmethod
    def print() -> None:
        """
        Pretty print the initialized sensors.
        """
        print("Sensors:")
        for sensor in Sensor.sensors:
            print(f"  {sensor.name} ({sensor.calibration.unit}) on {sensor.channel}")

    @staticmethod
    def parse(data: list[list[float | int]]) -> dict[str, list[float | int]]:
        """
        Apply each sensor's calibration to voltages from the NI box.
        """
        res: dict[str, list[float | int]] = {}
        for i, sensor in enumerate(Sensor.sensors):
            res[f"{sensor.name} ({sensor.calibration.unit})"] = [sensor.calibration.calibrate(d) for d in data[i]]
        return res
