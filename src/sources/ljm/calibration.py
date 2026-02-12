import math
from enum import Enum
from typing import ClassVar, Self

# Import the LabJack package
from labjack import ljm
from msgpack.exceptions import PackException

# A map between a channel name and
# the channel number of its negative channel
# in differential mode.
# -1 (assigned to odd-numbered channels) means
# they only work in single-ended mode
# or as the negative channel in differential mode.
CHANNEL_TO_NEGATIVE_CHANNEL = {
    "AIN0": 1,
    "AIN1": -1,
    "AIN2": 3,
    "AIN3": -1,
    "AIN4": 5,
    "AIN5": -1,
    "AIN6": 7,
    "AIN7": -1,
    "AIN8": 9,
    "AIN9": -1,
    "AIN10": 11,
    "AIN11": -1,
    "AIN12": 13,
    "AIN13": -1,
}


class Connection(Enum):
    """
    Represents how a sensor is wired into the LabJack box.
    """

    SINGLE = 0  # Referenced Single Ended
    DIFFERENTIAL = 1


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

    def __init__(
        self,
        voltage: float | int,
        resistance: float | int,
        B: float | int,
        r_inf: float | int,
    ):
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
        return (
            f"Thermistor({self.voltage}, {self.resistance}, {self.B}, x) ({self.unit})"
        )


class Sensor:
    sensors: ClassVar[list[Self]] = []

    name: str
    channel: str
    input_range: float | int
    connection: Connection
    calibration: Calibration

    """
    Represents a sensor plugged into the LabJack box.
    Instantiating members of this class sets up the sensors used with the static methods.
    """

    def __init__(
        self,
        name: str,
        channel: str,
        input_range: float | int,
        connection: Connection,
        calibration: Calibration,
    ) -> None:
        self.name = name
        self.channel = channel  # LabJack Box Channel, e.g. AIN0
        self.input_range = (
            # Voltage Range for the LabJack Box
            # 10, 1, 0.1, or 0.01
            input_range
        )
        self.connection = connection  # Single or Differential
        self.calibration = calibration

        for sensor in Sensor.sensors:
            if sensor.name == self.name:
                raise KeyError(f"Duplicate sensors named {self.name}")

        Sensor.sensors.append(self)

    @staticmethod
    def setup(handle: int) -> tuple[int, list[str]]:
        """
        Set up the LabJack analog input task with the initialized sensors.
        Returns an int, the number of addresses set up,
        and a list of strings, the names of the addresses set up.
        """

        list_of_addresses = []

        for sensor in Sensor.sensors:
            ljm.eWriteName(handle, f"{sensor.channel}_RANGE", sensor.input_range)
            negChannelValue = ljm.constants.GND
            if sensor.connection == Connection.DIFFERENTIAL:
                negChannelValue = CHANNEL_TO_NEGATIVE_CHANNEL[sensor.channel]
                if negChannelValue == -1:
                    raise ValueError(f"Invalid negative channel for {sensor.channel}")
            ljm.eWriteName(handle, f"{sensor.channel}_NEGATIVE_CH", negChannelValue)
            list_of_addresses.append(sensor.channel)

        assert len(list_of_addresses) == len(Sensor.sensors)

        return len(list_of_addresses), list_of_addresses

    @staticmethod
    def print() -> None:
        """
        Pretty print the initialized sensors.
        """
        print("Sensors:")
        for sensor in Sensor.sensors:
            print(f"  {sensor.name} ({sensor.calibration.unit}) on {sensor.channel}")

    @staticmethod
    def parse(sensor_values: list[list[float | int]]) -> dict[str, list[float | int]]:
        """
        Apply each sensor's calibration to voltages from the LabJack box.
        """
        res: dict[str, list[float | int]] = {}
        for i, sensor in enumerate(Sensor.sensors):
            res[f"{sensor.name} ({sensor.calibration.unit})"] = [
                sensor.calibration.calibrate(d) for d in sensor_values[i]
            ]
        return res
