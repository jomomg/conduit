from typing import Literal
from fastapi import APIRouter, Body
from sqlalchemy.exc import IntegrityError
from .articles import get_user_or_404, DatabaseDep, ActiveUserDep
from ..schemas.articles import Profile

router = APIRouter()


@router.get("/profiles/{username}", response_model=dict[Literal["profile"], Profile])
async def get_profile_with_username(username: str, db: DatabaseDep):
    """Get user profile"""

    user = get_user_or_404(db, username)
    return {"profile": user.profile}


@router.post(
    "/profiles/{username}/follow",
    response_model=dict[Literal["profile"], Profile],
)
async def follow_profile(username: str, db: DatabaseDep, current_user: ActiveUserDep):
    """Follow a profile"""

    profile_to_follow = get_user_or_404(db, username).profile
    current_profile = current_user.profile
    profile_to_follow.set_as_follower(current_profile)
    db.commit()
    setattr(profile_to_follow, "following", True)
    return {"profile": profile_to_follow}


@router.delete(
    "/profiles/{username}/follow", response_model=dict[Literal["profile"], Profile]
)
async def unfollow_profile(username: str, db: DatabaseDep, current_user: ActiveUserDep):
    """Unfollow a profile"""

    profile_to_unfollow = get_user_or_404(db, username).profile
    current_profile = current_user.profile
    profile_to_unfollow.remove_as_follower(current_profile)
    db.commit()
    return {"profile": profile_to_unfollow}
