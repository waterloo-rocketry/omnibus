
#Write a nominal test

from .omnibus_Data_Types import DAQMessage, CANMessage

import pytest

class test_DAQ_message:

    def test_DAQ_valid_data():
        myDict = {
            "timestamp" : 12345.2,
            "data": {
            "Sensor A": [3.4, 3, 2]
            },
            "relative_timestamps": [1,3,3],
            "sample_rate": 1000,
            "message_version": 2
            }
        msg = DAQMessage(**myDict)
        assert myDict == msg.model_dump()

    def test_DAQ_relative_timestamps_and_sensor_data_length():
        myDict = {
        "timestamp" : 12345.2,
        "data": {
        "Sensor A": [3.4, 3, 2]
        },
        "relative_timestamps": [1,3],
        "sample_rate": 1000,
        "message_version": 3
        }
        with pytest.raises(ValueError):
            msg = DAQMessage(**myDict)
         
    def test_DAQ_empty_list():
        with pytest.raises(TypeError):
            msg = DAQMessage({})

    def test_DAQ_invalid_type():
        with pytest.raises(TypeError):
            msg = DAQMessage("not a dict")

class test_CAN_Message:
    def test_CAN_valid_data():
        my_dict = {
        "board_type_id": "102s",
        "msg_type": "sensorB",
        "msg_prio": "HIGH",
        "board_inst_id": "432b",
        "can_msg": {"a" : 34},
        "parsely": "2",
        "message_version": 3
        }

        msg =  CANMessage(**my_dict)
        assert msg.model_dump() == my_dict

    def test_CAN_invalid_msg_prio():
        my_dict = {
        "board_type_id": "102s",
        "msg_type": "sensorB",
        "msg_prio": "important",
        "board_inst_id": "432b",
        "can_msg": {"a" : 34},
        "parsely": "2",
        "message_version": 3
        }

        with pytest .raises(TypeError):
            msg = CANMessage(**my_dict)

    def test_CAN_empty_list():
        with pytest.raises(TypeError):
            msg = CANMessage({})
            

    def test_CAN_invalid_type():
        with pytest.raises(TypeError):
            msg = CANMessage("not a dict")
