from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import get_current_user
from app.modules.verification.schema import TrustScoreResponse, VerificationVote
from app.modules.verification.service import get_score, record_vote

router = APIRouter(prefix="/verification", tags=["verification"])


@router.post("/vote")
async def vote(payload: VerificationVote, user=Depends(get_current_user)) -> dict:
    if payload.target_type not in {"place", "post"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid target_type")
    if payload.vote not in {"up", "down"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid vote")

    await record_vote(target_type=payload.target_type, target_id=payload.target_id, vote=payload.vote)
    return {"status": "ok"}


@router.get("/score", response_model=TrustScoreResponse)
async def score(target_type: str, target_id: str) -> TrustScoreResponse:
    up, down, s = await get_score(target_type=target_type, target_id=target_id)
    return TrustScoreResponse(target_type=target_type, target_id=target_id, up=up, down=down, score=s)
