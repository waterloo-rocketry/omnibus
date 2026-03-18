import math
from enum import Enum
from typing import ClassVar, Self

# Import the LabJack package
from labjack import ljm
from msgpack.exceptions import PackException

# A map between a channel name and
# the channel number of its negative channel
# in differential mode.
CHANNEL_TO_NEGATIVE_CHANNEL = {
    "AIN87": 95,
    "AIN86": 94,
    "AIN85": 93,
    "AIN84": 92,
    "AIN83": 91,
    "AIN82": 90,
    "AIN81": 89,
    "AIN80": 88,
    "AIN71": 79,
    "AIN70": 78,
    "AIN69": 77,
    "AIN68": 76,
    "AIN67": 75,
    "AIN66": 74,
    "AIN65": 73,
    "AIN64": 72,
    "AIN53": 61,
    "AIN52": 60,
    "AIN51": 59,
    "AIN50": 58,
    "AIN49": 57,
    "AIN48": 56,
    "AIN55": 63,
    "AIN54": 62,
    "AIN96": 104,
    "AIN97": 105,
    "AIN98": 106,
    "AIN99": 107,
    "AIN100": 108,
    "AIN101": 109,
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
        
        if (not self.input_range in [10, 1, 0.1, 0.01]):
            raise ValueError(f"Invalid input range {self.input_range} for sensor {self.name}. Must be 10, 1, 0.1, or 0.01.")

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
                try:
                    negChannelValue = CHANNEL_TO_NEGATIVE_CHANNEL[sensor.channel]
                except KeyError:
                    raise ValueError(
                        f"{sensor.channel} does not have a valid negative channel."
                    )
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
