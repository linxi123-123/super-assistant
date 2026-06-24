from __future__ import annotations

from pydantic import BaseModel


class MemoryItem(BaseModel):
    id: str
    memory_type: str
    content: str
    sensitivity_level: str
    user_confirmed: bool = False
