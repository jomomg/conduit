from fastapi import APIRouter
from sqlalchemy.exc import IntegrityError
from .articles import get_user_or_404, DatabaseDep, ActiveUserDep, set_following_status
from ..schemas.articles import Profile

router = APIRouter()


@router.get("/profiles/{username}", response_model=Profile)
async def get_username(username: str, db: DatabaseDep):
    """Get user profile"""

    user = get_user_or_404(db, username)
    return user.profile


@router.post("/profiles/{username}/follow", response_model=Profile)
async def follow_profile(username: str, db: DatabaseDep, current_user: ActiveUserDep):
    """Follow a profile"""

    profile_to_follow = get_user_or_404(db, username).profile
    current_profile = current_user.profile
    profile_to_follow.set_as_follower(current_profile)
    db.commit()
    return profile_to_follow


@router.delete("/profiles/{username}/follow", response_model=Profile)
async def unfollow_profile(username: str, db: DatabaseDep, current_user: ActiveUserDep):
    """Unfollow a profile"""

    profile_to_follow = get_user_or_404(db, username).profile
    current_profile = current_user.profile
    profile_to_follow.remove_as_follower(current_profile)
    db.commit()
    return profile_to_follow
