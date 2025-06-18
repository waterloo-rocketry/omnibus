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

    def __init__(self, csv_name, matching_pattern, reading_signature=None):
        """Initialize the field with a name, a matching pattern, and a reading signature.
        The matching pattern is a dictionary of keys and values that MUST appear inside the message payload being matched,
        and if it's sub-dictioinaries, use . like data.sensor_id.
        The reading signature is a string that describes the path to the value we want to extract from the payload.
        Again, if it's a sub-dictionary, use . like data.value.
        """

        self.csv_name = csv_name
        self.matching_pattern = matching_pattern
        self.reading_signature = reading_signature

        if reading_signature is None:
            raise ValueError("reading_signature must be provided.")


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
            # This should not raise an error, as we might be checking many fields against one candidate
            return None # Indicate no match

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
