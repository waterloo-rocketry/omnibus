# This file tracks message_types.h in canlib. I just copy and pasted cause I want a quick
# and dirty CAN message decoder and not much more.
#                  byte 0      byte 1       byte 2         byte 3                  byte 4          byte 5          byte 6          byte 7
# GENERAL CMD:    TSTAMP_MS_H TSTAMP_MS_M  TSTAMP_MS_L    COMMAND_TYPE            None            None            None            None
# VENT_VALVE_CMD:  TSTAMP_MS_H TSTAMP_MS_M  TSTAMP_MS_L    VENT_VALVE_STATE        None            None            None            None
# INJ_VALVE_CMD:   TSTAMP_MS_H TSTAMP_MS_M  TSTAMP_MS_L    INJ_VALVE_STATE         None            None            None            None
# ALT_ARM_CMD:     TSTAMP_MS_H TSTAMP_MS_M  TSTAMP_MS_L    ALT_ARM_STATE & #       None            None            None            None
# DEBUG_MSG:       TSTAMP_MS_H TSTAMP_MS_M  TSTAMP_MS_L    DEBUG_LEVEL | LINUM_H   LINUM_L         MESSAGE_DEFINED MESSAGE_DEFINED MESSAGE_DEFINED
# DEBUG_PRINTF:    ASCII       ASCII        ASCII          ASCII                   ASCII           ASCII           ASCII           ASCII
# VENT_VALVE_STAT: TSTAMP_MS_H TSTAMP_MS_M  TSTAMP_MS_L    VENT_VALVE_STATE        CMD_VALVE_STATE None            None            None
# INJ_VALVE_STAT:  TSTAMP_MS_H TSTAMP_MS_M  TSTAMP_MS_L    INJ_VALVE_STATE         CMD_VALVE_STATE None            None            None
# ALT_ARM_STAT:    TSTAMP_MS_H TSTAMP_MS_M  TSTAMP_MS_L    ALT_ARM_STATE & #       V_DROGUE_H      V_DROGUE_L      V_MAIN_H        V_MAIN_L
# BOARD_STAT:      TSTAMP_MS_H TSTAMP_MS_M  TSTAMP_MS_L    ERROR_CODE              BOARD_DEFINED   BOARD_DEFINED   BOARD_DEFINED   BOARD_DEFINED
# SENSOR_ACC:      TSTAMP_MS_M TSTAMP_MS_L  VALUE_X_H      VALUE_X_L               VALUE_Y_H       VALUE_Y_L       VALUE_Z_H       VALUE_Z_L
# SENSOR_GYRO:     TSTAMP_MS_M TSTAMP_MS_L  VALUE_X_H      VALUE_X_L               VALUE_Y_H       VALUE_Y_L       VALUE_Z_H       VALUE_Z_L
# SENSOR_MAG:      TSTAMP_MS_M TSTAMP_MS_L  VALUE_X_H      VALUE_X_L               VALUE_Y_H       VALUE_Y_L       VALUE_Z_H       VALUE_Z_L
# SENSOR_ANALOG:   TSTAMP_MS_M TSTAMP_MS_L  SENSOR_ID      VALUE_H                 VALUE_L         None            None            None
# SENSOR_ALTITUDE: TSTAMP_MS_H TSTAMP_MS_M  TSTAMP_MS_L    ALTITUDE_H              ALTITUDE_HM     ALTITUDE_LM     ALTITUDE_L      None
# LEDS_ON:         None        None         None           None                    None            None            None            None
# LEDS_OFF:        None        None         None           None                    None            None            None            None
# FILL_LVL:        TSTAMP_MS_H TSTAMP_MS_M  TSTAMP_MS_L    FILL_LEVEL              DIRECTION       None            None            None

msg_type_hex = {
    "GENERAL_CMD": 0x060,
    "ACTUATOR_CMD": 0x0C0,
    "ALT_ARM_CMD": 0x140,

    "DEBUG_MSG": 0x180,
    "DEBUG_PRINTF": 0x1E0,

    "ALT_ARM_STATUS": 0x440,
    "ACTUATOR_STATUS": 0x460,
    "GENERAL_BOARD_STATUS": 0x520,
    "RECOVERY_STATUS": 0x540,

    "SENSOR_TEMP": 0x540,
    "SENSOR_ALTITUDE": 0x560,
    "SENSOR_ACC": 0x580,
    "SENSOR_ACC2": 0x5A0,
    "SENSOR_GYRO": 0x5E0,
    "SENSOR_MAG": 0x640,
    "SENSOR_ANALOG": 0x6A0,

    "GPS_TIMESTAMP": 0x6C0,
    "GPS_LATITUDE": 0x6E0,
    "GPS_LONGITUDE": 0x700,
    "GPS_ALTITUDE": 0x720,
    "GPS_INFO": 0x740,

    "FILL_LVL": 0x780,

    "LEDS_ON": 0x7E0,
    "LEDS_OFF": 0x7C0,
}
msg_type_str = {v: k for k, v in msg_type_hex.items()}

board_id_hex = {
    "DUMMY": 0x00,
    "INJECTOR": 0x01,
    "INJECTOR_SPARE": 0x02,
    "LOGGER": 0x03,
    "LOGGER_SPARE": 0x04,
    "RADIO": 0x05,
    "RADIO_SPARE": 0x06,
    "SENSOR": 0x07,
    "SENSOR_SPARE": 0x08,
    "USB": 0x09,
    "USB_SPARE": 0x0A,
    "VENT": 0x0B,
    "VENT_SPARE": 0x0C,
    "GPS": 0x0D,
    "GPS_SPARE": 0x0E,
    "FILL": 0x0F,
    "FILL_SPARE": 0x010,
    "ARMING": 0x11,
    "ARMING_SPARE": 0X12,
    "PAPA": 0x13,
    "PAPA_SPARE": 0x14,
    "ROCKET_PI": 0x15,
    "ROCKET_PI_2": 0x16,
    "ROCKET_PI_2_SPARE": 0x18,
    "SENSOR_2": 0x19,
    "SENSOR_2_SPARE": 0x1A,
    "SENSOR_3": 0x1B,
    "SENSOR_4": 0x1C,
    "TEMP_SENSE": 0x15,
    "TEMP_SENSE_SPARE": 0x16,
    "LOGGER_2": 0x1D,
    "RLCS": 0x1E
}
board_id_str = {v: k for k, v in board_id_hex.items()}

# GEN_CMD
gen_cmd_hex = {"BUS_DOWN_WARNING": 0}
gen_cmd_str = {v: k for k, v in gen_cmd_hex.items()}

# ACTUATOR_CMD/STATUS STATES
actuator_states_hex = {
    "ACTUATOR_OPEN":  0,
    "ACTUATOR_CLOSED": 1,
    "ACTUATOR_UNK": 2,
    "ACTUATOR_ILLEGAL": 3
}
actuator_states_str = {v: k for k, v in actuator_states_hex.items()}

# ARM_CMD/STATUS STATES
arm_states_hex = {
    "DISARMED": 0,
    "ARMED": 1
}
arm_states_str = {v: k for k, v in arm_states_hex.items()}


# BOARD GENERAL STATUS ERROR CODES
# ERROR CODE (byte 3)         (byte4)             (byte 5)            (byte 6)            (byte 7)
board_stat_hex = {
    "E_NOMINAL": 0,                   # x                x                   x                   x

    "E_BUS_OVER_CURRENT": 1,          # mA_high          mA_low              x                   x
    "E_BUS_UNDER_VOLTAGE": 2,         # mV_high          mV_low              x                   x
    "E_BUS_OVER_VOLTAGE": 3,          # mV_high          mV_low              x                   x

    "E_BATT_UNDER_VOLTAGE": 4,        # mV_high          mV_low              x                   x
    "E_BATT_OVER_VOLTAGE": 5,         # mV_high          mV_low              x                   x

    "E_BOARD_FEARED_DEAD": 6,         # board_id         x                   x                   x
    "E_NO_CAN_TRAFFIC": 7,            # time_s_high      time_s_low          x                   x
    "E_MISSING_CRITICAL_BOARD": 8,    # board_id         x                   x                   x
    "E_RADIO_SIGNAL_LOST": 9,         # time_s_high      time_s_low          x                   x

    "E_ACTUATOR_STATE": 10,              # expected_state   valve_state         x                   x
    "E_CANNOT_INIT_DACS": 11,         # x                x                   x                   x
    "E_VENT_POT_RANGE": 12,            # lim_upper (mV)   lim_lower (mV)      pot (mV)            x

    "E_LOGGING": 13,                  # x                x                   x                   x
    "E_GPS": 14,                      # x                x                   x                   x
    "E_SENSOR": 15,                   # sensor_id        x                   x                   x

    "E_ILLEGAL_CAN_MSG": 16,          # x                x                   x                   x
    "E_SEGFAULT": 17,                 # x                x                   x                   x
    "E_UNHANDLED_INTERRUPT": 18,      # x                x                   x                   x
    "E_CODING_FUCKUP": 19,            # x                x                   x                   x

    "E_BATT_OVER_CURRENT": 20         # mA_high          mA_low              x                   x
}
board_stat_str = {v: k for k, v in board_stat_hex.items()}

# SENSOR_ID
sensor_id_hex = {
    "SENSOR_IMU1": 0,
    "SENSOR_IMU2": 1,
    "SENSOR_BARO": 2,
    "SENSOR_PRESSURE_OX": 3,
    "SENSOR_PRESSURE_CC": 4,
    "SENSOR_VENT_BATT": 5,
    "SENSOR_INJ_BATT": 6,
    "SENSOR_ARM_BATT_1": 7,
    "SENSOR_ARM_BATT_2": 8,
    "SENSOR_BATT_CURR": 9,
    "SENSOR_BUS_CURR": 10,
    "SENSOR_VELOCITY": 11,
    "SENSOR_MAG_1": 12,
    "SENSOR_MAG_2": 13,
    "SENSOR_ROCKET_BATT": 14,
    "SENSOR_PRESSURE_PNEUMATICS": 15,
    "SENSOR_VENT_TEMP": 16,
    "SENSOR_RADIO_CURR": 18
}
sensor_id_str = {v: k for k, v in sensor_id_hex.items()}

fill_direction_hex = {
    "FILLING": 0,
    "EMPTYING": 1,
}
fill_direction_str = {v: k for k, v in fill_direction_hex.items()}

actuator_id_hex = {
    "VENT_VALVE": 0,
    "INJECTOR_VALVE": 1,
    "MAMA": 2,
    "PICAM": 3,
    "CANBUS": 4,
}
actuator_id_str = {v: k for k, v in actuator_id_hex.items()}
