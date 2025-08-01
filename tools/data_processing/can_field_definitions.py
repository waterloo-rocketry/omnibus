# Class that we can use to match a data packet to a field in the output csv
# The matching_pattern describes the elements of a dictionary from a msgpacked payload, and the values they should have. Fields to be matched are seperated by periods for heirarchy
# Ex: {"msg_type": "SENSOR_ANALOG", "data.sensor_id": "SENSOR_PRESSURE_OX"} will ensure the msg_type is SENSOR_ANALOG, that there is a data feild, and that the data feild has a sensor_id feild equal to SENSOR_PRESSURE_OX
# Note: this differs from the way the data is stored in the msgpacked payload, which is a dictionary of dictionaries, instead of a single dictionary with keys period seperated to represent the heirarchy
# The reading_signature provides a direction to where the data we want to extract is
# Ex: "data.value" will return the value feild of the data feild of the msgpacked payload
# Ex2: "data.req_state" will return the req_state feild of the data feild of the msgpacked payload

# Run with -test to run tests
from typing import Self
import argparse
from copy import deepcopy
from string import Template
from typing import Optional, List


class CanProcessingField:
    """A class to represent a field in the CAN data that we can export as a CSV column. Has a matching pattern to try and see if a message payload matches the field (for CAN fields logged in the .log file by a parsley instance), and extracts the value from the payload if it does. These should be though of as an abstraction to explain what a message represents ex: the pneumatic pressure can be found at "msg_type": "SENSOR_ANALOG", "data.sensor_id": "SENSOR_PRESSURE_PNEUMATICS" and we want to extract "data.value" from it."""

    def __init__(self, csv_name, matching_pattern, reading_signature):
        """Initialize the field with a name, a matching pattern, and a reading signature. The matching pattern is a dictionary of keys and values that MUST appear inside the message payload being matched, and if it's sub-dictioinaries, use . like data.sensor_id. The reading signature is a string that describes the path to the value we want to extract from the payload. Again, if it's a sub-dictionary, use . like data.value."""

        self.csv_name = csv_name
        self.matching_pattern = matching_pattern
        self.reading_signature = reading_signature

    def __repr__(self):
        return f"<ProcessingField {self.csv_name} (matching: {self.matching_pattern}, reading: {self.reading_signature})>"

    def __str__(self):
        return self.__repr__()

    def match(self, candidate) -> Optional['CanProcessingField']:
        """Check if the candidate message payload matches the matching pattern"""

        matched_instance: Self | None = None
        for key, value in self.matching_pattern.items():
            if key == 'board_type_id' and value == 'ANY':
                matched_instance = deepcopy(self)
                candidate_board_name = candidate['board_type_id'].lower()
                if isinstance(matched_instance.csv_name,Template):
                    matched_instance.csv_name = matched_instance.csv_name.substitute(board_type_id=candidate_board_name)
                continue # Keep will override data
            running_key = key
            checking = candidate
            while running_key.find(".") != -1:
                nested_key, running_key = running_key.split(".", 1)
                if nested_key not in checking:
                    return None
                checking = checking[nested_key]
            if running_key not in checking or checking[running_key] != value:
                return None
        return matched_instance if matched_instance else self

    def read(self, candidate):
        """Read the value from the candidate message payload, if it matches the matching pattern. If it doesn't, raises an error."""

        if not self.match(candidate):  # first double check that it's the right thing
            raise ValueError(
                f"Can't read from a candidate that doesn't match the matching pattern {self.matching_pattern} for the data {candidate}")

        running_key = self.reading_signature
        checking = candidate
        while running_key.find(".") != -1:
            nested_key, running_key = running_key.split(".", 1)
            if nested_key not in checking:
                return None
            checking = checking[nested_key]
        if running_key not in checking:
            return None

        return checking[running_key]


# Fields can be discovered by using the field_peeking.py script
# Then you define the CSV name, paste the signature from the discovery script, and choose a value from the dictionary you want to export

CAN_FIELDS: List[CanProcessingField] = [
    # 0x10
    CanProcessingField("sensor_mag_y", {
                       "board_type_id": "PROCESSOR", "msg_type": "SENSOR_MAG_Y", "data.imu_id": "IMU_PROC_ALTIMU10"}, "data.mag"),
    # 0x11
    CanProcessingField("sensor_mag_y", {
                       "board_type_id": "PROCESSOR", "msg_type": "SENSOR_MAG_Y", "data.imu_id": "IMU_PROC_ALTIMU10"}, "data.mag"),
    # 0x12
    CanProcessingField("sensor_mag_z", {
                       "board_type_id": "PROCESSOR", "msg_type": "SENSOR_MAG_Z", "data.imu_id": "IMU_PROC_ALTIMU10"}, "data.mag"),

    # 0x014
    CanProcessingField("battery_current", {
                       "board_type_id": "POWER", "msg_type": "SENSOR_ANALOG", "data.sensor_id": "SENSOR_BATT_CURR"}, "data.value"),
    CanProcessingField("battery_voltage", {
                       "board_type_id": "POWER", "msg_type": "SENSOR_ANALOG", "data.sensor_id": "SENSOR_BATT_VOLT"}, "data.value"),
    CanProcessingField("charge_current", {
                       "board_type_id": "POWER", "msg_type": "SENSOR_ANALOG", "data.sensor_id": "SENSOR_CHARGE_CURR"}, "data.value"),
    CanProcessingField("motor_current", {
                       "board_type_id": "POWER", "msg_type": "SENSOR_ANALOG", "data.sensor_id": "SENSOR_MOTOR_CURR"}, "data.value"),
]

# General Fields is for everyboard shared field, it will based on the board id
# dynamic added it use Template as csv name with field ${board_type_id}, other than 
# that it stay same as auto_fields.
general_fields = [
    {
        "temp_name": "${board_type_id}_board_status",
        "signature": {'msg_type': 'GENERAL_BOARD_STATUS'},
        "fields": ["data.general_error_bitfield", "data.board_error_bitfield"]
    }, # 0x001
    {
        "temp_name": "${board_type_id}_state_est_data",
        "signature": {'msg_type': 'STATE_EST_DATA'},
        "fields": ["data.state_id", "data.data"]
    }, # 0x01A
]

# Auto-add fields with multiple values for the same signature
# the signature is the same as usual, the base name is the prefix used, and then the fields are used for the part of the data and for labeling
auto_fields = [
    {
        "base_name": "altimeter_stratologger",
        "signature": {'board_type_id': 'ARMING', 'msg_type': 'ALT_ARM_STATUS', "data.alt_id": "ALTIMETER_STRATOLOGGER"},
        "fields": ["data.alt_arm_state", "data.drogue_v", "data.main_v"]
    }, # 0x008
    {
        "base_name": "altimeter_raven",
        "signature": {'board_type_id': 'ARMING', 'msg_type': 'ALT_ARM_STATUS', "data.alt_id": "ALTIMETER_RAVEN"},
        "fields": ["data.alt_arm_state", "data.drogue_v", "data.main_v"]
    }, # 0x008
    {
        "base_name": "x_imu",
        "signature": {'board_type_id': 'PROCESSOR', 'msg_type': 'SENSOR_IMU_X', "data.imu_id": "IMU_PROC_ALTIMU10"},
        "fields": ["data.linear_accel", "data.angular_velocity"]
    }, # 0x00d
    {
        "base_name": "y_imu",
        "signature": {'board_type_id': 'PROCESSOR', 'msg_type': 'SENSOR_IMU_Y', "data.imu_id": "IMU_PROC_ALTIMU10"},
        "fields": ["data.linear_accel", "data.angular_velocity"]
    }, # 0x00e
    {
        "base_name": "z_imu",
        "signature": {'board_type_id': 'PROCESSOR', 'msg_type': 'SENSOR_IMU_Z', "data.imu_id": "IMU_PROC_ALTIMU10"},
        "fields": ["data.linear_accel", "data.angular_velocity"]
    }, # 0x00f
    {
        "base_name": "power_baro",
        "signature": {'board_type_id': 'POWER', 'msg_type': 'SENSOR_BARO', "data.imu_id": "IMU_PROC_ALTIMU10"},
        "fields": ["data.pressure", "data.temp"]
    }, # 0x013
    {
        "base_name": "gps_timestamp",
        "signature": {'board_type_id': 'GPS', 'msg_type': 'GPS_TIMESTAMP'},
        "fields": ["data.hrs", "data.mins", "data.secs", "data.dsecs"]
    }, # 0x015
    {
        "base_name": "gps_lat",
        "signature": {'board_type_id': 'GPS', 'msg_type': 'GPS_LATITUDE'},
        "fields": ["data.degs", "data.mins", "data.dmins"]
    }, # 0x016
    {
        "base_name": "gps_lon",
        "signature": {'board_type_id': 'GPS', 'msg_type': 'GPS_LONGITUDE'},
        "fields": ["data.degs", "data.mins", "data.dmins"]
    }, # 0x017
    {
        "base_name": "gps_alt",
        "signature": {'board_type_id': 'GPS', 'msg_type': 'GPS_ALTITUDE'},
        "fields": ["data.ailtitude"]
    }, # 0x018
]

# Add the auto fields to the CAN_FIELDS
for field in auto_fields:
    for subfield in field["fields"]:
        CAN_FIELDS.append(CanProcessingField(
            f"{field['base_name']}_{subfield.split('.')[-1]}", field["signature"], subfield))

for field in general_fields:
    field["signature"]["board_type_id"] = "ANY"
    for subfield in field["fields"]:
        CAN_FIELDS.append(CanProcessingField(
            Template(f"{field['temp_name']}_{subfield.split('.')[-1]}"), field["signature"], subfield))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run tests for field_definitions.py")
    parser.add_argument("--test", action="store_true", help="Run tests")
    TESTING = parser.parse_args().test

    if not TESTING:
        print("This file is not meant to be run directly. Run main.py instead.")
        exit(1)

    # test matching
    correct_matching_pattern = {"msg_type": "SENSOR_ANALOG", "data.sensor_id": "SENSOR_PRESSURE_OX"}
    incorrect_matching_pattern = {"msg_type": "SENSOR_ANALOG",
                                  "data.sensor_id": "SENSOR_PRESSURE_FUEL"}
    inexistant_matching_pattern = {"msg_type": "SENSOR_ANALOG",
                                   "mangoes.pears": "SENSOR_PRESSURE_OX"}

    correct_reading_signature = "data.value"
    incorrect_reading_signature = "data.req_state"
    inexistant_reading_signature = "data.mangoes"

    cmatch_cread = CanProcessingField(
        "ox tank", correct_matching_pattern, correct_reading_signature)
    cmatch_iread = CanProcessingField(
        "ox tank", correct_matching_pattern, incorrect_reading_signature)
    cmatch_ixread = CanProcessingField(
        "ox tank", correct_matching_pattern, inexistant_reading_signature)
    imatch_cread = CanProcessingField(
        "ox tank", incorrect_matching_pattern, correct_reading_signature)
    imatch_iread = CanProcessingField(
        "ox tank", incorrect_matching_pattern, incorrect_reading_signature)
    imatch_ixread = CanProcessingField(
        "ox tank", incorrect_matching_pattern, inexistant_reading_signature)
    ixmatch_cread = CanProcessingField(
        "ox tank", inexistant_matching_pattern, correct_reading_signature)
    ixmatch_iread = CanProcessingField(
        "ox tank", inexistant_matching_pattern, incorrect_reading_signature)
    ixmatch_ixread = CanProcessingField(
        "ox tank", inexistant_matching_pattern, inexistant_reading_signature)

    # example candidates
    correct_candidate = {"msg_type": "SENSOR_ANALOG", "data": {
        "sensor_id": "SENSOR_PRESSURE_OX", "value": 100}}
    missing_value_candidate = {"msg_type": "SENSOR_ANALOG",
                               "data": {"sensor_id": "SENSOR_PRESSURE_OX"}}
    false_candidate = {"msg_type": "SENSOR_ANALOG",
                       "data": {"sensor_id": "NOT_THE_ONE", "value": 100}}
    missing_data_candidate = {"msg_type": "SENSOR_ANALOG"}

    print("Testing matching")
    print("Correct input matching")
    assert cmatch_cread.match(correct_candidate)
    assert cmatch_iread.match(correct_candidate)
    assert cmatch_ixread.match(correct_candidate)
    assert not imatch_cread.match(correct_candidate)
    assert not imatch_iread.match(correct_candidate)
    assert not imatch_ixread.match(correct_candidate)
    assert not ixmatch_cread.match(correct_candidate)
    assert not ixmatch_iread.match(correct_candidate)
    assert not ixmatch_ixread.match(correct_candidate)
    print("Correct input reading")
    assert cmatch_cread.read(correct_candidate) == 100
    assert cmatch_iread.read(correct_candidate) == None
    assert cmatch_ixread.read(correct_candidate) == None
    assert imatch_cread.read(correct_candidate) == None
    assert imatch_iread.read(correct_candidate) == None
    assert imatch_ixread.read(correct_candidate) == None
    assert ixmatch_cread.read(correct_candidate) == None
    assert ixmatch_iread.read(correct_candidate) == None
    assert ixmatch_ixread.read(correct_candidate) == None
    print("Incorrect input matching")
    assert not cmatch_cread.match(false_candidate)
    assert not imatch_cread.match(false_candidate)
    assert not ixmatch_cread.match(false_candidate)
    print("Missing value input reading")
    assert cmatch_cread.read(missing_value_candidate) == None
    print("Missing data input matching")
    assert not cmatch_cread.match(missing_data_candidate)

    print("All tests passed!")
