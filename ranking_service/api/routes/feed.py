from fastapi import APIRouter

from ranking_service.domain.schemas import RankFeedRequest, RankFeedResponse
from ranking_service.services.scoring import rank_candidates

router = APIRouter(prefix="/feed", tags=["feed"])


@router.post("/rank", response_model=RankFeedResponse)
async def rank_feed(payload: RankFeedRequest) -> RankFeedResponse:
    ranked_profile_ids = rank_candidates(
        user_id=payload.user_id,
        user_interest_ids=payload.user_interest_ids,
        candidates=payload.candidates,
        excluded_ids=payload.excluded_ids,
        limit=payload.limit,
    )
    return RankFeedResponse(ranked_profile_ids=ranked_profile_ids)
