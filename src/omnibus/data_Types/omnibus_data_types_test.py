
#Write a nominal test

from omnibus_Data_Types import DAQMessage


import pytest

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

def test_DAQ_empty_list():
    with pytest.raises(TypeError):
         msg = DAQMessage({})
         

def test_DAQ_invalid_type():
    with pytest.raises(TypeError):
        msg = DAQMessage("not a dict")




