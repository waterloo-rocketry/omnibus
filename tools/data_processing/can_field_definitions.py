# Class that we can use to match a data packet to a field in the output csv
# The matching_pattern describes the elements of a dictionary from a msgpacked payload, and the values they should have. Fields to be matched are seperated by periods for heirarchy
# Ex: {"msg_type": "SENSOR_ANALOG", "data.sensor_id": "SENSOR_PRESSURE_OX"} will ensure the msg_type is SENSOR_ANALOG, that there is a data feild, and that the data feild has a sensor_id feild equal to SENSOR_PRESSURE_OX
# Note: this differs from the way the data is stored in the msgpacked payload, which is a dictionary of dictionaries, instead of a single dictionary with keys period seperated to represent the heirarchy
# The reading_signature provides a direction to where the data we want to extract is
# Ex: "data.value" will return the value feild of the data feild of the msgpacked payload
# Ex2: "data.req_state" will return the req_state feild of the data feild of the msgpacked payload

# Run with -test to run tests
import argparse


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

    def match(self, candidate):
        """Check if the candidate message payload matches the matching pattern"""

        for key, value in self.matching_pattern.items():
            running_key = key
            checking = candidate
            while running_key.find(".") != -1:
                nested_key, running_key = running_key.split(".", 1)
                if nested_key not in checking:
                    return False
                checking = checking[nested_key]
            if running_key not in checking or checking[running_key] != value:
                return False
        return True

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

CAN_FIELDS = [
    CanProcessingField("ox_tank_pressure", {
                       "msg_type": "SENSOR_ANALOG", "data.sensor_id": "SENSOR_PRESSURE_OX"}, "data.value"),
    CanProcessingField("pneumatics_pressure", {
                       "msg_type": "SENSOR_ANALOG", "data.sensor_id": "SENSOR_PRESSURE_PNEUMATICS"}, "data.value"),
    CanProcessingField("vent_temp", {"msg_type": "SENSOR_ANALOG",
                       "data.sensor_id": "SENSOR_VENT_TEMP"}, "data.value"),
    CanProcessingField("vent_ox_pressure", {
                       'board_id': 'SENSOR_VENT', 'msg_type': 'SENSOR_ANALOG', 'data.sensor_id': 'SENSOR_PRESSURE_OX'}, "data.req_state"),
    CanProcessingField("vent_valve_req_status", {
                       "msg_type": "ACTUATOR_STATUS", "data.actuator": "ACTUATOR_VENT_VALVE"}, "data.req_state"),
    CanProcessingField("vent_valve_cur_status", {
                       "msg_type": "ACTUATOR_STATUS", "data.actuator": "ACTUATOR_VENT_VALVE"}, "data.cur_state"),
    CanProcessingField("injector_valve_req_status", {
                       "msg_type": "ACTUATOR_STATUS", "data.actuator": "ACTUATOR_INJECTOR_VALVE"}, "data.req_state"),
    CanProcessingField("injector_valve_cur_status", {
                       "msg_type": "ACTUATOR_STATUS", "data.actuator": "ACTUATOR_INJECTOR_VALVE"}, "data.cur_state"),
    CanProcessingField("battery_current", {
                       "board_id": "CHARGING", "msg_type": "SENSOR_ANALOG", "data.sensor_id": "SENSOR_BATT_CURR"}, "data.value"),
    CanProcessingField("bus_current", {
                       "board_id": "CHARGING", "msg_type": "SENSOR_ANALOG", "data.sensor_id": "SENSOR_BUS_CURR"}, "data.value"),
    CanProcessingField("charge_current", {
                       "board_id": "CHARGING", "msg_type": "SENSOR_ANALOG", "data.sensor_id": "SENSOR_CHARGE_CURR"}, "data.value"),
    CanProcessingField("battery_voltage", {
                       "board_id": "CHARGING", "msg_type": "SENSOR_ANALOG", "data.sensor_id": "SENSOR_BATT_VOLT"}, "data.value"),
    CanProcessingField("ground_voltage", {
                       "board_id": "CHARGING", "msg_type": "SENSOR_ANALOG", "data.sensor_id": "SENSOR_GROUND_VOLT"}, "data.value"),
    CanProcessingField("injector_battery_voltage", {
                       "board_id": "ACTUATOR_INJ", "msg_type": "SENSOR_ANALOG", "data.sensor_id": "SENSOR_BATT_VOLT"}, "data.value"),
    CanProcessingField("injector_board_status", {
                       "board_id": "ACTUATOR_INJ", "msg_type": "GENERAL_BOARD_STATUS"}, "data.status"),
    CanProcessingField("injector_valve_status", {
                       "board_id": "ACTUATOR_INJ", "msg_type": "ACTUATOR_STATUS", "data.actuator": "ACTUATOR_INJECTOR_VALVE"}, "data.req_state"),
    CanProcessingField("charging_board_status", {
                       "board_id": "CHARGING", "msg_type": "GENERAL_BOARD_STATUS"}, "data.status"),
    CanProcessingField("cc_pressure", {
                       'board_id': 'SENSOR_INJ', 'msg_type': 'SENSOR_ANALOG', 'data.sensor_id': 'SENSOR_PRESSURE_CC'}, 'data.value'),
    CanProcessingField("barometer", {
                       'board_id': 'SENSOR_INJ', 'msg_type': 'SENSOR_ANALOG', 'data.sensor_id': 'SENSOR_BARO'}, "data.value"),

    # These GPS fields should maybe be formatted differently, but this works great :)
    CanProcessingField("gps_timestamp_hours", {
                       'board_id': 'GPS', 'msg_type': 'GPS_TIMESTAMP'}, "data.hrs"),
    CanProcessingField("gps_timestamp_minutes", {
                       'board_id': 'GPS', 'msg_type': 'GPS_TIMESTAMP'}, "data.mins"),
    CanProcessingField("gps_timestamp_seconds", {
                       'board_id': 'GPS', 'msg_type': 'GPS_TIMESTAMP'}, "data.secs"),
    CanProcessingField("gps_lat_degrees", {'board_id': 'GPS',
                       'msg_type': 'GPS_LATITUDE'}, "data.degs"),
    CanProcessingField("gps_lat_minutes", {'board_id': 'GPS',
                       'msg_type': 'GPS_LATITUDE'}, "data.mins"),
    # idk what dmins is for
    CanProcessingField("gps_lat_dmins", {'board_id': 'GPS',
                       'msg_type': 'GPS_LATITUDE'}, "data.dmins"),
    CanProcessingField("gps_lat_direction", {'board_id': 'GPS',
                       'msg_type': 'GPS_LATITUDE'}, "data.direction"),
    CanProcessingField("gps_lon_degrees", {'board_id': 'GPS',
                       'msg_type': 'GPS_LONGITUDE'}, "data.degs"),
    CanProcessingField("gps_lon_minutes", {'board_id': 'GPS',
                       'msg_type': 'GPS_LONGITUDE'}, "data.mins"),
    CanProcessingField("gps_lon_dmins", {'board_id': 'GPS',
                       'msg_type': 'GPS_LONGITUDE'}, "data.dmins"),
    CanProcessingField("gps_lon_direction", {'board_id': 'GPS',
                       'msg_type': 'GPS_LONGITUDE'}, "data.direction"),
    CanProcessingField("gps_altitude_meters", {
                       'board_id': 'GPS', 'msg_type': 'GPS_ALTITUDE'}, "data.altitude"),

]


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
