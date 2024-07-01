from datetime import datetime
from typing import List
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


class OutputDataObj(BaseModel):
    created_date:datetime
    status:str
    link:str
    name:str
    type:str


class ListOutputDataObj(BaseModel):
    collection:List[OutputDataObj] = []