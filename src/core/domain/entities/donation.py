from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class Donation(BaseModel):
    id: Optional[int] = None
    user_id: Optional[int] = None
    amount: float
    currency: str = "USD"
    platform: str
    transaction_id: Optional[str] = None
    message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
