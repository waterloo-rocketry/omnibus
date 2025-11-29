from pydantic import BaseModel
from typing import Literal, Union
from enum import Enum

class RLCSv3Message(BaseModel):
    id: int
    
    data: dict[str, str | int | float]
    message_version: Literal[2]

