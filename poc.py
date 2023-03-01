# import message_types as mt

class BitString:
    """
    Store the bits of the message data that we have yet to parse, and let us chop off
    arbitrary-length sections from the front. We need to operate at the bit level since some
    fields don't take up a whole byte (eg. DEBUG_MSG's DEBUG_LEVEL) and some fields are split
    weirdly across bytes (eg. DEBUG_MSG's LINUM, a 12-bit value).
    """
    def __init__(self, data):
        self.length = len(data) * 8 # length in bits
        # store the data as an int (in python ints are unbounded and this lets us do bitwise manipulations)
        self.data = int.from_bytes(data, 'big')

    def pop(self, field_length) -> bytes:
        """
        Returns the next field_length bits of data as a bytes object.

        The data will be LSB-aligned, so for example asking for 12 bits will return:
        0000BBBB BBBBBBBB
        where B represents a data bit.
        """
        if self.length < field_length:
            raise IndexError
        self.length -= field_length
        res = self.data >> (self.length) # extract the field_length most significant bits
        self.data = self.data & ((1 << self.length) - 1) # and then mask them out
        return res.to_bytes((field_length + 7) // 8, 'big') # and convert to a bytes object

class Field:
    """
    Abstract base class for a field in a message.
    """
    def __init__(self, name, length):
        self.name = name
        self.length = length # length in bits

    def decode(self, data):
        """
        Convert self.length bits of data (returned in the format given by BitString.pop)
        to the corresponding python value of the field. This value could be a number, string,
        etc. depending on the specific field type.
        """
        raise NotImplementedError

    def encode(self, value):
        """
        Convert value to self.length bits of data (in an LSB-aligned bytes object) to
        build a message. Raise a ValueError with an appropiate message if this is not possible.
        """
        raise NotImplementedError

class Numeric(Field):
    def __init__(self, name, length, scale = 1, signed = False):
        super().__init__(name, length)
        self.scale = scale
        self.signed = signed

    def decode(self, data):
        val = int.from_bytes(data, 'big', signed = self.signed)
        return val * self.scale

    def encode(self, value):
        value //= self.scale
        if not self.signed:
            if value >= 1 << self.length:
                raise ValueError(f"Value {value} is too large for {self.length} unsigned bits.")
            if value < 0:
                raise ValueError(f"Cannot encode negative value {value} in unsigned field.")
        else:
            if value >= 1 << (self.length - 1):
                raise ValueError(f"Value {value} is too large for {self.length} signed bits.")
            if value < -1 << (self.length - 1):
                raise ValueError(f"Value {value} is too small for {self.length} signed bits.")
        return value.to_bytes((self.length + 7) // 8, 'big', self.signed)

class Enum(Field):
    def __init__(self, name, length, map_val_num):
        super().__init__(name, length)

        for k, v in map_val_num.items():
            if v < 0:
                raise ValueError(f"Mapping for key {k} should not be negative.")
            if v >= 1 << self.length:
                raise ValueError(f"Mapping for key {k} is too large to fit in {self.length} bits.")

        self.map_val_num = map_val_num
        self.map_num_val = {v: k for k, v in self.map_val_num.items()}

    def decode(self, data):
        num = int.from_bytes(data, 'big', signed=False)
        return self.map_num_val[num]

    def encode(self, value):
        if value not in self.map_val_num:
            raise ValueError(f"Value {value} not in mapping.")
        return self.map_val_num[value].to_bytes((self.length + 7) // 8, 'big')

class Ascii(Field):
    def __init__(self, name, length):
        super().__init__(name, length)

    def decode(self, data):
        return data.decode('ascii')
    
    def encode(self, value):
        # i need to go test to ensure my sanity
        if self.length < len(value):
            raise ValueError(f"String {value} is too large for {self.length}")
        if not value.isascii():
            raise UnicodeEncodeError(f"Value contains non-ascii characters")
        return value.encode('ascii')

TIMESTAMP_2 = Numeric("time", 16, scale=0.001, signed=True)
TIMESTAMP_3 = Numeric("time", 24, scale=0.001)

FIELDS = {
    "GENERAL_CMD": [TIMESTAMP_3, Enum("command", 8, mt.gen_cmd_hex)],
    "ACTUATOR_CMD": [TIMESTAMP_3, Enum("actuator", 8, mt.actuator_id_hex), Enum("state", 8, mt.actuator_states_hex)],
    "ALT_ARM_CMD": [TIMESTAMP_3, Enum("state", 4, mt.arm_states_hex), Numeric("number", 4)],
    "RESET_CMD": [TIMESTAMP_3, Enum("id", 8, mt.board_id_hex)],

    "DEBUG_MSG": [TIMESTAMP_3, Numeric("level", 4), Numeric("line", 12), Ascii("data", 24)],
    "DEBUG_PRINTF": [Ascii("string", 64)], # entirely ascii
    "DEBUG_RADIO_CMD": [Ascii("string", 64)], # entirely ascii

    "ACTUATOR_STAT": [TIMESTAMP_3, Enum("actuator", 8, mt.actuator_id_hex), Enum("req_state", 8, mt.actuator_states_hex), Enum("cur_state", 8, mt.actuator_states_hex)],
    "ALT_ARM_STAT": [TIMESTAMP_3, Enum("state", 4, mt.arm_states_hex), Numeric("number", 4), Numeric("drogue_v", 16, signed=True), Numeric("main_v", 16, signed=True)],
    "BOARD_STAT": [TIMESTAMP_3, Enum("stat", 8, mt.board_stat_hex) ], # TODO HALP

    "SENSOR_TEMP": [TIMESTAMP_3, Numeric("sensor", 8), Numeric("temperature", 24, scale=0.001, signed=True)],
    "SENSOR_ALTITUDE": [TIMESTAMP_3, Numeric("altitude", 32, signed=False)], # weird signed 2s compliment subtraction
    "SENSOR_ACC": [TIMESTAMP_2, Numeric("x", 16, scale=0.0001, signed=True), Numeric("y", 16, scale=0.0001, signed=True), Numeric("z", 16, scale=0.0001, signed=True)], # weird a / (2**16) * 8 going on but also x16 for ACC2 ?? or just a parlsey thing, signed in parsley parse
    "SENSOR_GYRO": [TIMESTAMP_2, Numeric("x", 16, scale=0.03, signed=True), Numeric("y", 16, scale=0.03, signed=True), Numeric("z", 16, scale=0.03, signed=True)], # unsure about rounding, signed in parsley parse
    "SENSOR_MAG": [TIMESTAMP_2, Numeric("x", 16, signed=True), Numeric("y", 16, signed=True), Numeric("z", 16, signed=True)], # they're signed in parsley parse
    "SENSOR_ANALOG": [TIMESTAMP_2, Enum("id", 8, mt.sensor_id_hex), Numeric("value", 16, signed=True)],

    "GPS_TIMESTAMP": [TIMESTAMP_3, Numeric("hours", 8), Numeric("minutes", 8), Numeric("seconds", 8), Numeric("dseconds", 8)],
    "GPS_LATITUDE": [TIMESTAMP_3, Numeric("degrees", 8), Numeric("minutes", 8), Numeric("dminutes", 16, signed=True), Ascii("direction", 8)],
    "GPS_LONGITUDE": [TIMESTAMP_3, Numeric("degrees", 8), Numeric("minutes", 8), Numeric("dminutes", 16, signed=True), Ascii("direction", 8)],
    "GPS_ALTITUDE": [TIMESTAMP_3, Numeric("altitude", 16, signed=True), Numeric("daltitude", 8), Ascii("unit", 8)],
    "GPS_INFO": [TIMESTAMP_3, Numeric("numsat", 8), Numeric("quality", 8)],

    "FILL_LVL": [TIMESTAMP_3, Numeric("level", 8), Enum("direction", 8, mt.fill_direction_hex)],

    "RADI_VALUE": [TIMESTAMP_3, Numeric("board", 8), Numeric("radi", 16, signed=True)],

    "LEDS_ON": [],
    "LEDS_OFF": []
}

def parse(msg_sid, msg_data):
    msg_type = mt.msg_type_str[msg_sid & 0x7e0]
    board_id = mt.board_id_str[msg_sid & 0x1f]
    msg_data = BitString(msg_data)

    result = {"msg_type": msg_type, "board_id": board_id, "data": {}}
    for field in FIELDS[msg_type]:
        result["data"][field.name] = field.decode(msg_data.pop(field.length))

    return result

#  *                  byte 0      byte 1      byte 2      byte 3                byte 4         byte 5             byte 6          byte 7
#  * GENERAL_CMD:     TSTAMP_MS_H TSTAMP_MS_M TSTAMP_MS_L COMMAND_TYPE          None           None               None            None
#  * ACTUATOR_CMD:    TSTAMP_MS_H TSTAMP_MS_M TSTAMP_MS_L ACTUATOR_ID           ACTUATOR_STATE None               None            None
#  * ALT_ARM_CMD:     TSTAMP_MS_H TSTAMP_MS_M TSTAMP_MS_L ALT_ARM_STATE & #     None           None               None            None
#  * RESET_CMD:       TSTAMP_MS_H TSTAMP_MS_M TSTAMP_MS_L BOARD_ID              None           None               None            None
#  *
#  * DEBUG_MSG:       TSTAMP_MS_H TSTAMP_MS_M TSTAMP_MS_L DEBUG_LEVEL | LINUM_H LINUM_L        MESSAGE_DEFINED    MESSAGE_DEFINED MESSAGE_DEFINED
#  * DEBUG_PRINTF:    ASCII       ASCII       ASCII       ASCII                 ASCII          ASCII              ASCII           ASCII
#  * DEBUG_RADIO_CMD: ASCII       ASCII       ASCII       ASCII                 ASCII          ASCII              ASCII           ASCII
#  *
#  * ACTUATOR_STAT:   TSTAMP_MS_H TSTAMP_MS_M TSTAMP_MS_L ACTUATOR_ID           ACTUATOR_STATE REQ_ACTUATOR_STATE None            None
#  * ALT_ARM_STAT:    TSTAMP_MS_H TSTAMP_MS_M TSTAMP_MS_L ALT_ARM_STATE & #     V_DROGUE_H     V_DROGUE_L         V_MAIN_H        V_MAIN_L
#  * BOARD_STAT:      TSTAMP_MS_H TSTAMP_MS_M TSTAMP_MS_L ERROR_CODE            BOARD_DEFINED  BOARD_DEFINED      BOARD_DEFINED   BOARD_DEFINED
#  *
#  * SENSOR_TEMP:     TSTAMP_MS_H TSTAMP_MS_M TSTAMP_MS_L SENSOR_NUM            TEMP_H         TEMP_M             TEMP_L          None
#  * SENSOR_ALTITUDE: TSTAMP_MS_H TSTAMP_MS_M TSTAMP_MS_L ALTITUDE_H            ALTITUDE_MH    ALTITUDE_ML        ALTITUDE_L      None
#  * SENSOR_ACC:      TSTAMP_MS_M TSTAMP_MS_L VALUE_X_H   VALUE_X_L             VALUE_Y_H      VALUE_Y_L          VALUE_Z_H       VALUE_Z_L
#  * SENSOR_GYRO:     TSTAMP_MS_M TSTAMP_MS_L VALUE_X_H   VALUE_X_L             VALUE_Y_H      VALUE_Y_L          VALUE_Z_H       VALUE_Z_L
#  * SENSOR_MAG:      TSTAMP_MS_M TSTAMP_MS_L VALUE_X_H   VALUE_X_L             VALUE_Y_H      VALUE_Y_L          VALUE_Z_H       VALUE_Z_L
#  * SENSOR_ANALOG:   TSTAMP_MS_M TSTAMP_MS_L SENSOR_ID   VALUE_H               VALUE_L        None               None            None
#  *
#  * GPS_TIMESTAMP:   TSTAMP_MS_H TSTAMP_MS_M TSTAMP_MS_L UTC_HOURS             UTC_MINUTES    UTC_SECONDS        UTC_DSECONDS    None
#  * GPS_LAT:         TSTAMP_MS_H TSTAMP_MS_M TSTAMP_MS_L DEGREES               MINUTES        DMINUTES_H         DIMNUTES_L      N/S DIRECTION
#  * GPS_LON:         TSTAMP_MS_H TSTAMP_MS_M TSTAMP_MS_L DEGREES               MINUTES        DMINUTES_H         DIMNUTES_L      E/W DIRECTION
#  * GPS_ALT:         TSTAMP_MS_H TSTAMP_MS_M TSTAMP_MS_L ALT_H                 ALT_L          ALT_DEC            UNITS           None
#  * GPS_INFO:        TSTAMP_MS_H TSTAMP_MS_M TSTAMP_MS_L NUM_SAT               QUALITY        None               None            None
#  *
#  * FILL_LVL:        TSTAMP_MS_H TSTAMP_MS_M TSTAMP_MS_L FILL_LEVEL            DIRECTION      None               None            None
#  *
#  * RADI_VALUE:      TSTAMP_MS_H TSTAMP_MS_M TSTAMP_MS_L RADI_BOARD            RADI_HIGH      RADI_LOW           None            None
#  *
#  * LEDS_ON:         None        None        None        None                  None           None               None            None
#  * LEDS_OFF:        None        None        None        None                  None           None               None            None
#  *
