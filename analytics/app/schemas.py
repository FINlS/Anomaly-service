from datetime import datetime
from pydantic import BaseModel, IPvAnyAddress

class TrackIn(BaseModel):
    page_id: str
    user_id: str
    ip: IPvAnyAddress
    timestamp: datetime
    user_agent: str | None = None