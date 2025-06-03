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

    def __init__(self, csv_name, matching_pattern, reading_signature=None, can_id_bit_range=None):
        """Initialize the field with a name, a matching pattern, and a reading signature or CAN ID bit range.
        The matching pattern is a dictionary of keys and values that MUST appear inside the message payload being matched,
        and if it's sub-dictioinaries, use . like data.sensor_id.
        The reading signature is a string that describes the path to the value we want to extract from the payload.
        Again, if it's a sub-dictionary, use . like data.value.
        The can_id_bit_range is a tuple (start_bit, end_bit) for extracting data directly from the CAN ID.
        """

        self.csv_name = csv_name
        self.matching_pattern = matching_pattern
        self.reading_signature = reading_signature
        self.can_id_bit_range = can_id_bit_range

        if reading_signature is None and can_id_bit_range is None:
            raise ValueError("Either reading_signature or can_id_bit_range must be provided.")
        if reading_signature is not None and can_id_bit_range is not None:
             raise ValueError("Only one of reading_signature or can_id_bit_range can be provided.")


    def __repr__(self):
        return f"<ProcessingField {self.csv_name} (matching: {self.matching_pattern}, reading: {self.reading_signature}, can_id_bit_range: {self.can_id_bit_range})>"

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
            # This should not raise an error, as we might be checking many fields against one candidate
            return None # Indicate no match

        if self.can_id_bit_range is not None:
            if 'can_id' not in candidate:
                return None # Cannot extract from can_id if not present

            can_id = candidate['can_id']
            start_bit, end_bit = self.can_id_bit_range

            # Ensure start_bit is greater than or equal to end_bit for bit range extraction
            if start_bit < end_bit:
                 # Swap if necessary, or handle as an error depending on desired behavior
                 # For now, let's assume the range is inclusive [start, end] where start >= end
                 # If the user provides (27, 28) for bits 28:27, we should handle it.
                 # Let's assume the range is [MSB, LSB] inclusive.
                 msb, lsb = start_bit, end_bit
            else:
                 msb, lsb = start_bit, end_bit

            num_bits = msb - lsb + 1
            # Extract the bits: shift right by lsb, then mask with a mask of num_bits length
            extracted_value = (can_id >> lsb) & ((1 << num_bits) - 1)

            # Special handling for priority field
            if self.csv_name == "priority":
                priority_map = {
                    0b00: "Highest",
                    0b01: "High",
                    0b10: "Medium",
                    0b11: "Low"
                }
                return priority_map.get(extracted_value, "Unknown")

            return extracted_value

        elif self.reading_signature is not None:
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
        else:
            # Should not reach here due to __init__ checks, but as a fallback
            return None


# Fields can be discovered by using the field_peeking.py script
# Then you define the CSV name, paste the signature from the discovery script, and choose a value from the dictionary you want to export

CAN_FIELDS = [
    # CAN 2.0B Fields (29-bit ID)
    CanProcessingField("priority", {}, can_id_bit_range=(28, 27)),
    CanProcessingField("message_type", {}, can_id_bit_range=(26, 18)),
    CanProcessingField("board_type_id", {}, can_id_bit_range=(15, 8)),
    CanProcessingField("board_instance_id", {}, can_id_bit_range=(7, 0)),

    # Existing CAN 2.0A and other fields (payload-based)
    CanProcessingField("ox_tank_pressure", {
                       "msg_type": "SENSOR_ANALOG", "data.sensor_id": "SENSOR_PRESSURE_OX"}, reading_signature="data.value"),
    CanProcessingField("pneumatics_pressure", {
                       "msg_type": "SENSOR_ANALOG", "data.sensor_id": "SENSOR_PRESSURE_PNEUMATICS"}, reading_signature="data.value"),
    CanProcessingField("vent_temp", {"msg_type": "SENSOR_ANALOG",
                       "data.sensor_id": "SENSOR_VENT_TEMP"}, reading_signature="data.value"),
    CanProcessingField("vent_ox_pressure", {
                       'board_id': 'SENSOR_VENT', 'msg_type': 'SENSOR_ANALOG', 'data.sensor_id': 'SENSOR_PRESSURE_OX'}, reading_signature="data.req_state"),
    CanProcessingField("vent_valve_req_status", {
                       "msg_type": "ACTUATOR_STATUS", "data.actuator": "ACTUATOR_VENT_VALVE"}, reading_signature="data.req_state"),
    CanProcessingField("vent_valve_cur_status", {
                       "msg_type": "ACTUATOR_STATUS", "data.actuator": "ACTUATOR_VENT_VALVE"}, reading_signature="data.cur_state"),
    CanProcessingField("injector_valve_req_status", {
                       "msg_type": "ACTUATOR_STATUS", "data.actuator": "ACTUATOR_INJECTOR_VALVE"}, reading_signature="data.req_state"),
    CanProcessingField("injector_valve_cur_status", {
                       "msg_type": "ACTUATOR_STATUS", "data.actuator": "ACTUATOR_INJECTOR_VALVE"}, reading_signature="data.cur_state"),
    CanProcessingField("battery_current", {
                       "board_id": "CHARGING", "msg_type": "SENSOR_ANALOG", "data.sensor_id": "SENSOR_BATT_CURR"}, reading_signature="data.value"),
    CanProcessingField("bus_current", {
                       "board_id": "CHARGING", "msg_type": "SENSOR_ANALOG", "data.sensor_id": "SENSOR_BUS_CURR"}, reading_signature="data.value"),
    CanProcessingField("charge_current", {
                       "board_id": "CHARGING", "msg_type": "SENSOR_ANALOG", "data.sensor_id": "SENSOR_CHARGE_CURR"}, reading_signature="data.value"),
    CanProcessingField("battery_voltage", {
                       "board_id": "CHARGING", "msg_type": "SENSOR_ANALOG", "data.sensor_id": "SENSOR_BATT_VOLT"}, reading_signature="data.value"),
    CanProcessingField("ground_voltage", {
                       "board_id": "CHARGING", "msg_type": "SENSOR_ANALOG", "data.sensor_id": "SENSOR_GROUND_VOLT"}, reading_signature="data.value"),
    CanProcessingField("injector_battery_voltage", {
                       "board_id": "ACTUATOR_INJ", "msg_type": "SENSOR_ANALOG", "data.sensor_id": "SENSOR_BATT_VOLT"}, reading_signature="data.value"),
    CanProcessingField("injector_board_status", {
                       "board_id": "ACTUATOR_INJ", "msg_type": "GENERAL_BOARD_STATUS"}, reading_signature="data.status"),
    CanProcessingField("injector_valve_status", {
                       "board_id": "ACTUATOR_INJ", "msg_type": "ACTUATOR_STATUS", "data.actuator": "ACTUATOR_INJECTOR_VALVE"}, reading_signature="data.req_state"),
    CanProcessingField("charging_board_status", {
                       "board_id": "CHARGING", "msg_type": "GENERAL_BOARD_STATUS"}, reading_signature="data.status"),
    CanProcessingField("cc_pressure", {
                       'board_id': 'SENSOR_INJ', 'msg_type': 'SENSOR_ANALOG', 'data.sensor_id': 'SENSOR_PRESSURE_CC'}, reading_signature='data.value'),
    CanProcessingField("barometer", {
                       'board_id': 'SENSOR_INJ', 'msg_type': 'SENSOR_ANALOG', 'data.sensor_id': 'SENSOR_BARO'}, reading_signature="data.value"),
]

# Auto-add fields with multiple values for the same signature
# the signature is the same as usual, the base name is the prefix used, and then the fields are used for the part of the data and for labeling
auto_fields = [
    {
        "base_name": "gps_lat",
        "signature": {'board_id': 'GPS', 'msg_type': 'GPS_LATITUDE'},
        "fields": ["data.degs", "data.mins", "data.dmidminsnutes", "data.direction"]
    },
    {
        "base_name": "gps_lon",
        "signature": {'board_id': 'GPS', 'msg_type': 'GPS_LONGITUDE'},
        "fields": ["data.degs", "data.mins", "data.dmins", "data.direction"]
    },
    {
        "base_name": "gps_timestamp",
        "signature": {'board_id': 'GPS', 'msg_type': 'GPS_TIMESTAMP'},
        "fields": ["data.hrs", "data.mins", "data.secs"]
    },
    {
        "base_name": "sensor_vent_acc",
        "signature": {'board_id': 'SENSOR_VENT', 'msg_type': 'SENSOR_ACC'},
        "fields": ["data.time", "data.x", "data.y", "data.z"]
    },
    {
        "base_name": "sensor_vent_mag",
        "signature": {'board_id': 'SENSOR_VENT', 'msg_type': 'SENSOR_MAG'},
        "fields": ["data.time", "data.x", "data.y", "data.z"]
    },
    {
        "base_name": "sensor_vent_gyro",
        "signature": {'board_id': 'SENSOR_VENT', 'msg_type': 'SENSOR_GYRO'},
        "fields": ["data.time", "data.x", "data.y", "data.z"]
    },
    {
        "base_name": "sensor_inj_acc",
        "signature": {'board_id': 'SENSOR_INJ', 'msg_type': 'SENSOR_ACC'},
        "fields": ["data.time", "data.x", "data.y", "data.z"]
    },
    {
        "base_name": "sensor_inj_mag",
        "signature": {'board_id': 'SENSOR_INJ', 'msg_type': 'SENSOR_MAG'},
        "fields": ["data.time", "data.x", "data.y", "data.z"]
    },
    {
        "base_name": "sensor_inj_gyro",
        "signature": {'board_id': 'SENSOR_INJ', 'msg_type': 'SENSOR_GYRO'},
        "fields": ["data.time", "data.x", "data.y", "data.z"]
    },
]

# Add the auto fields to the CAN_FIELDS
for field in auto_fields:
    for subfield in field["fields"]:
        CAN_FIELDS.append(CanProcessingField(
            f"{field['base_name']}_{subfield.split('.')[-1]}", field["signature"], reading_signature=subfield))

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

    # Test cases for CAN ID bit range extraction
    # Example CAN 2.0B ID: Priority=01 (High), Message Type=123 (decimal), Board Type ID=45, Board Instance ID=67
    # Binary: 01 0001111011 00 00101101 01000011
    # Prio (28:27): 01 (1)
    # Msg Type (26:18): 000111101 (125) - Note: My manual calculation was wrong, it's 125
    # Reserved (17:16): 00 (0)
    # Board Type ID (15:8): 00101101 (45)
    # Board Instance ID (7:0): 01000011 (67)
    # Combined 29-bit ID (binary): 010001111011000010110101000011
    # Combined 29-bit ID (decimal): 888888883 (decimal)
    can_id_20b_example = 888888883 # 0b010001111011000010110101000011

    can_field_prio = CanProcessingField("priority", {}, can_id_bit_range=(28, 27))
    can_field_msg_type = CanProcessingField("message_type", {}, can_id_bit_range=(26, 18))
    can_field_board_type = CanProcessingField("board_type_id", {}, can_id_bit_range=(15, 8))
    can_field_board_instance = CanProcessingField("board_instance_id", {}, can_id_bit_range=(7, 0))

    # Test candidate with CAN ID
    candidate_with_can_id = {"can_id": can_id_20b_example, "msg_type": "SOME_TYPE", "data": {"value": 999}}
    candidate_without_can_id = {"msg_type": "SOME_TYPE", "data": {"value": 999}}


    print("Testing CAN ID bit range extraction")
    assert can_field_prio.read(candidate_with_can_id) == "High"
    assert can_field_msg_type.read(candidate_with_can_id) == 125
    assert can_field_board_type.read(candidate_with_can_id) == 45
    assert can_field_board_instance.read(candidate_with_can_id) == 67

    print("Testing CAN ID bit range extraction with missing can_id")
    assert can_field_prio.read(candidate_without_can_id) is None
    assert can_field_msg_type.read(candidate_without_can_id) is None
    assert can_field_board_type.read(candidate_without_can_id) is None
    assert can_field_board_instance.read(candidate_without_can_id) is None


    # Test cases for existing functionality (matching and reading signature)
    cmatch_cread = CanProcessingField(
        "ox tank", correct_matching_pattern, reading_signature=correct_reading_signature)
    cmatch_iread = CanProcessingField(
        "ox tank", correct_matching_pattern, reading_signature=incorrect_reading_signature)
    cmatch_ixread = CanProcessingField(
        "ox tank", correct_matching_pattern, reading_signature=inexistant_reading_signature)
    imatch_cread = CanProcessingField(
        "ox tank", incorrect_matching_pattern, reading_signature=correct_reading_signature)
    imatch_iread = CanProcessingField(
        "ox tank", incorrect_matching_pattern, reading_signature=incorrect_reading_signature)
    imatch_ixread = CanProcessingField(
        "ox tank", incorrect_matching_pattern, reading_signature=inexistant_reading_signature)
    ixmatch_cread = CanProcessingField(
        "ox tank", inexistant_matching_pattern, reading_signature=correct_reading_signature)
    ixmatch_iread = CanProcessingField(
        "ox tank", inexistant_matching_pattern, reading_signature=incorrect_reading_signature)
    ixmatch_ixread = CanProcessingField(
        "ox tank", inexistant_matching_pattern, reading_signature=inexistant_reading_signature)

    # example candidates
    correct_candidate = {"msg_type": "SENSOR_ANALOG", "data": {
        "sensor_id": "SENSOR_PRESSURE_OX", "value": 100, "req_state": "OPEN"}}
    missing_value_candidate = {"msg_type": "SENSOR_ANALOG",
                               "data": {"sensor_id": "SENSOR_PRESSURE_OX", "req_state": "OPEN"}}
    false_candidate = {"msg_type": "SENSOR_ANALOG",
                       "data": {"sensor_id": "NOT_THE_ONE", "value": 100, "req_state": "OPEN"}}
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
    assert cmatch_iread.read(correct_candidate) == "OPEN"
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
