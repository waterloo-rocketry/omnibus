from omnibus.data_types import DAQMessage, CANMessage, ParselyMessage
from parsley import message_types

import pytest

class TestDAQMessage:
    def test_DAQ_valid_data(self):
        myDict = {
            "timestamp" : 12345.2,
            "data": {
                "Sensor A": [3.4, 3, 2]
            },
            "relative_timestamps": [1,3,3],
            "sample_rate": 1000,
            "message_version": 3
            }
        msg = DAQMessage(**myDict)
        assert myDict == msg.model_dump()

    def test_DAQ_relative_timestamps_and_sensor_data_length(self):
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

    def test_DAQ_empty_list(self):
        with pytest.raises(TypeError):
            msg = DAQMessage({})

    def test_DAQ_invalid_type(self):
        with pytest.raises(TypeError):
            msg = DAQMessage("not a dict")

class TestCANMessage:
    def test_CAN_valid_data(self):
        my_dict = {
        "board_type_id": "RLCS_GLS",
        "msg_type": "SENSOR_MAG_X",
        "msg_prio": "LOW",
        "board_inst_id": "CANARD_B",
        "can_msg": {"a" : 34},
        "parsely": "2",
        "message_version": 3
        }

        msg =  CANMessage(**my_dict)
        assert msg.model_dump() == my_dict

    def test_CAN_invalid_data(self):
        my_dict = {
        "board_type_id": "RLCS_GLS",
        "msg_type": "hello?",
        "msg_prio": "important",
        "board_inst_id": "432b",
        "can_msg": {"a" : 34},
        "parsely": "2",
        "message_version": 3
        }

        with pytest.raises(ValueError):
            msg = CANMessage(**my_dict)

    def test_CAN_empty_list(self):
        with pytest.raises(TypeError):
            msg = CANMessage({})
        
            
    def test_CAN_invalid_type(self):
        with pytest.raises(TypeError):
            msg = CANMessage("not a dict")

class TestParselyMessage:
    def test_parsely_valid_data(self) -> None:
        my_dict = {
        "board_type_id": "INJ_SENSOR",
        "board_inst_id": "PAYLOAD",
        "msg_prio": "HIGH",
        "msg_type": "GENERAL_BOARD_STATUS",
        "data": {"direction": "NORTH"},
        "parsely": "2",
        "message_version": 3
        }

        msg =  ParselyMessage(**my_dict)
        assert msg.model_dump() == my_dict

    def test_parsely_invalid_data(self):
        my_dict = {
        "board_type_id": "102s",
        "board_inst_id": "432b",
        "msg_prio": "not important",
        "msg_type": "the type of message",
        "data": {"direction": "NORTH"},
        "parsely": "2",
        "message_version": 3
        }

        with pytest.raises(ValueError):
            msg = ParselyMessage(**my_dict)

    def test_parsely_empty_list(self):
        with pytest.raises(TypeError):
            msg = ParselyMessage({})
            
    def test_parsely_invalid_type(self):
        with pytest.raises(TypeError):
            msg = ParselyMessage("not a dict")
