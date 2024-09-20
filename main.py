import jwt
from jwt.exceptions import InvalidTokenError
from typing import Annotated
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from .database import SessionMaker, engine
from .models import Base, User, Profile
from .schemas import (
    UserRegisterOut,
    UserOut,
    UserLogin,
    UserLoginOut,
    DecodedToken,
    UserRegisterIn,
    UserUpdate,
)
from .crud import add_to_db

TOKEN_EXPIRY_MINUTES = 120
SECRET_KEY = "TCEMfX9afLhjSPWHAhiipe2qfUxXW9OuQeWOXZKkGyBErBcFJJ"  # TODO move to .env
JWT_ALGORITHM = "HS256"

Base.metadata.create_all(bind=engine)

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db():
    db_session = SessionMaker()
    try:
        yield db_session
    finally:
        db_session.close()


def decode_token(token: str) -> DecodedToken | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        sub = payload.get("sub")
        if not sub:
            raise InvalidTokenError

    except InvalidTokenError:
        return None
    else:
        return DecodedToken(
            user_id=sub, email=payload.get("email"), username=payload.get("username")
        )


async def get_current_active_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    CredentialsException = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    decoded_token = decode_token(token)
    if not decoded_token:
        raise CredentialsException
    active_user = db.get(User, decoded_token.user_id)
    if not active_user:
        raise CredentialsException
    return active_user


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def get_user_by_email(db: Session, email: str) -> User | None:
    user = db.query(User).filter(User.email == email).first()
    return user


def create_access_token(token_payload: dict) -> str:
    payload = token_payload.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
    payload.update({"exp": expire})
    jwt_token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    return jwt_token


@app.get("/")
async def root():
    return {"message": "welcome to conduit"}


# get current user
@app.get("/api/user")
async def get_user(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> UserOut:
    return {
        "email": current_user.email,
        "username": current_user.username,
        "bio": current_user.profile.bio,
        "image": current_user.profile.image,
    }


# register user
@app.post("/api/users", response_model=UserRegisterOut)
async def register_user(
    user: Annotated[UserRegisterIn, Body(embed=True)], db: Session = Depends(get_db)
):
    existing = get_user_by_email(db, user.email)
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
@app.post("/api/login", response_model=UserLoginOut)
async def login(
    user: Annotated[UserLogin, Body(embed=True)], db: Session = Depends(get_db)
):
    unauthorized_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
    current_user = get_user_by_email(db, user.email)
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
@app.put("/api/user", response_model=UserUpdate, response_model_exclude={"password"})
async def update_user(
    user: Annotated[UserUpdate, Body(embed=True)],
    active_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    profile_attrs = ["bio", "image"]
    existing = get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
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
