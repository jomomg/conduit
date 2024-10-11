from typing import Annotated, Literal
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from ..dependencies import get_db, get_current_active_user, create_access_token
from ..models import User, Profile
from ..schemas.users import (
    UserRegisterOut,
    UserOut,
    UserLogin,
    UserLoginOut,
    UserRegisterIn,
    UserUpdate,
)

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DatabaseDep = Annotated[Session, Depends(get_db)]
ActiveUserDep = Annotated[User, Depends(get_current_active_user)]


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def get_user_by_attribute(
    db: Session, attribute: Literal["email", "username"], value: str | None
) -> User | None:
    if value and attribute in ["email", "username"]:
        return db.query(User).filter_by(**{attribute: value}).first()
    return None


# get current user
@router.get("/user", response_model=UserOut)
async def get_user(current_user: Annotated[User, Depends(get_current_active_user)]):
    return {
        "email": current_user.email,
        "username": current_user.username,
        "bio": current_user.profile.bio,
        "image": current_user.profile.image,
    }


# register user
@router.post("/users", response_model=UserRegisterOut)
async def register_user(
    user: Annotated[UserRegisterIn, Body(embed=True)], db: Session = Depends(get_db)
):
    existing = get_user_by_attribute(db, "email", user.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
        )
    pwd_hash = get_password_hash(user.password)
    new_user = User(email=user.email, password_hash=pwd_hash, username=user.username)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    new_profile = Profile(user_id=new_user.id)
    db.add(new_profile)
    db.commit()
    return new_user


# login
@router.post("/users/login", response_model=UserLoginOut)
async def login(
    user: Annotated[UserLogin, Body(embed=True)], db: Session = Depends(get_db)
):
    unauthorized_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
    current_user = get_user_by_attribute(db, "email", user.email)
    if not current_user:
        raise unauthorized_exception

    if not verify_password(user.password, current_user.password_hash):
        raise unauthorized_exception

    user_payload = {
        "sub": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
    }

    token = create_access_token(user_payload)

    return {
        "email": current_user.email,
        "username": current_user.username,
        "token": token,
        "bio": current_user.profile.bio,
        "image": current_user.profile.image,
    }


# update_user
@router.put("/user", response_model=UserUpdate, response_model_exclude={"password"})
async def update_user(
    user: Annotated[UserUpdate, Body(embed=True)],
    active_user: ActiveUserDep,
    db: DatabaseDep,
):
    profile_attrs = ["bio", "image"]
    existing_email = get_user_by_attribute(db, "email", user.email)
    if existing_email and existing_email is not active_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
        )

    existing_username = get_user_by_attribute(db, "username", user.username)
    if existing_username and existing_username is not active_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists"
        )

    for key, value in user.model_dump(exclude_unset=True).items():
        if key in profile_attrs:
            setattr(active_user.profile, key, value)
        setattr(active_user, key, value)

    db.commit()
    db.refresh(active_user)
    return {
        "email": active_user.email,
        "username": active_user.username,
        "bio": active_user.profile.bio,
        "image": active_user.profile.image,
    }
