from typing import Literal, Self
from pydantic import BaseModel, model_validator
from parsley import message_types


class DAQMessage(BaseModel):
    """
    DAQmessage class, stores and validates all DAQ data.
    """

    timestamp: float
    data: dict[str, list[int | float]]
    relative_timestamps: list[int | float]
    sample_rate: int
    message_version: Literal[3]


    @model_validator(mode='after')
    def check_relative_timestamp_length(self) -> Self:
        """
        makes sure that all sensor data has the same length as the relative timestamps. 
        """

        for sensor, data_arr in self.data.items():
            if len(data_arr) != len(self.relative_timestamps):
                raise ValueError(f"Length of timestamps must match number of data points per sensor. " +
                                 f"Length of {sensor} data is {len(data_arr)}, while timestamps is {len(self.relative_timestamps)}\n")
        return self


class CANMessage(BaseModel):
    """
    CANMesage dataclass, holds and validates all can message data.
    """

    board_type_id: str
    msg_type: str
    msg_prio: str
    board_inst_id: str
    can_msg: dict
    parsely: str
    message_version: Literal[3]

    @model_validator(mode = 'after')
    def check_all_parsely_data(self) ->Self:
        """
        checks all parsely data in the object using the helper function
        """

        check_all_parsely_data_helper(self)

    
class ParselyMessage(BaseModel):
    """
    dataclass for parsely message, holds and validates all types below
    """

    board_type_id: str
    board_inst_id: str
    msg_prio: str
    msg_type: str
    data: dict
    parsely: str
    message_version: Literal[3]

    @model_validator(mode = 'after')
    def check_all_parsely_data(self) ->Self:
        """
        checks all parsely data in the object using the helper function
        """

        check_all_parsely_data_helper(self)

        return self


def check_all_parsely_data_helper(self):
    """
    takes an object and checks all parsely data if the string belongs 
    to the parsely library
    """

    message_data = [[self.board_type_id,message_types.board_type_id,"board_type_id"],
                        [self.board_inst_id,message_types.board_inst_id,"board_inst_id"],
                        [self.msg_prio,message_types.msg_prio,"msg_prio"],
                        [self.msg_type,message_types.msg_type,"msg_type"]]
        
    for current_data, proper_data, data_title in message_data:
        if (current_data not in proper_data):
                raise ValueError(f"{current_data} is not a valid {data_title}")
            
    return self

    