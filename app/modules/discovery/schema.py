from __future__ import annotations

from pydantic import BaseModel


class DiscoveryPlace(BaseModel):
    id: str
    name: str
    category: str
    lat: float
    lon: float
