from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime


class ChatEntry(BaseModel):
    question: str
    AI: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
