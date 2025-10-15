from typing import Optional, List
from pydantic import BaseModel


class AvatarItem(BaseModel):
    name: str
    url: str
    size_bytes: Optional[int] = None
    modified_ts: Optional[float] = None


class AvatarList(BaseModel):
    items: List[AvatarItem]
