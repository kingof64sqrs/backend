from __future__ import annotations

from pydantic import BaseModel, Field


class VerificationVote(BaseModel):
    target_type: str = Field(description="place|post")
    target_id: str
    vote: str = Field(description="up|down")


class TrustScoreResponse(BaseModel):
    target_type: str
    target_id: str
    up: int
    down: int
    score: float
