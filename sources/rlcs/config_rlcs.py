'''
MSG_INDEX: a list of all the data contained in one line from the RLCS, 
in the order in which they appear in the message. 
Used to help in parsing RLCS-format data.

e.g. "rlcs_main_batt_mv" is index 0 in MSG_INDEX, and it is represented
by the first four-digit hexadecimal number in the RLCS message. 
"ignition_primary_ma" is index 3 and maps to the fourth four-digit 
hexadecimal number in the RLCS message. 
'''
MSG_INDEX = [
    "rlcs_main_batt_mv",
    "rlcs_actuator_batt_mv",
    "healthy_actuators",
    "ignition_primary_ma",
    "ignition_secondary_ma",
    "fill_valve_state",
    "vent_valve_state",
    "injector_valve_state"
]
