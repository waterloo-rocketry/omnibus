

#import pydantic
from typing import Literal, Self
from pydantic import BaseModel, model_validator
#DAQMessage type includes typical omnibus message and 4 more literals

class DAQMessage(BaseModel):
    timestamp: float
    data: dict[str, list[int | float]]
    relative_timestamps: list[int | float]
    sample_rate: int
    message_version: Literal[2]

    @model_validator(mode='after')
    def check_relative_timestamp_length(self) -> Self:
        for sensor, data_arr in self.data.items():
            if len(data_arr) != len(self.relative_timestamps):
                raise ValueError(f"Length of timestamps must match number of data points per sensor. " +
                                 f"Length of {sensor} data is {len(data_arr)}, while timestamps is {len(self.relative_timestamps)}\n")
        return self
        



if __name__ == "__main__":
    dict = {
        "timestamp" : 12345.2,
        "data": {
            "Sensor A": [3.4, 3, 2]
        },
        "relative_timestamps": [1,3,4],
        "sample_rate": 1000,
        "message_version": 2
    }
    msg = DAQMessage(**dict)
    print(msg.model_dump())
