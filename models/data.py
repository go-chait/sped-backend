from pydantic import BaseModel
from enum import Enum

class DocType(Enum):
   LINK = 1
   PDF = 2
   

class StatusType(Enum):
    PENDING = 1
    FAILED = 2
    SCRAPE = 3
    

class DataObj(BaseModel):
    name:str
    type:DocType
    link:str
    status:StatusType