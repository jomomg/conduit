from typing import Annotated, Optional
import jwt
from sqlalchemy.orm import Session
from .database import SessionMaker
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timezone, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .models import User
from .schemas.users import DecodedToken

TOKEN_EXPIRY_MINUTES = 120
SECRET_KEY = "TCEMfX9afLhjSPWHAhiipe2qfUxXW9OuQeWOXZKkGyBErBcFJJ"  # TODO move to .env
JWT_ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")
auth_optional = OAuth2PasswordBearer(tokenUrl="/api/users/login", auto_error=False)

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_db():
    db_session = SessionMaker()
    try:
        yield db_session
    finally:
        db_session.close()


def decode_token(token: str) -> DecodedToken:
    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[JWT_ALGORITHM], options={"verify_exp": False}
        )
        sub = payload.get("sub")
        if not sub:
            raise InvalidTokenError

    except InvalidTokenError:
        raise credentials_exception
    else:
        return DecodedToken(
            user_id=sub, email=payload.get("email"), username=payload.get("username")
        )


def create_access_token(token_payload: dict) -> str:
    payload = token_payload.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
    payload.update({"exp": expire})
    jwt_token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    return jwt_token


async def get_user_from_token(token: str, db: Session) -> User:
    decoded_token = decode_token(token)
    if not decoded_token:
        raise credentials_exception
    active_user = db.get(User, decoded_token.user_id)
    if not active_user:
        raise credentials_exception
    return active_user


async def get_current_active_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:

    return await get_user_from_token(token, db)


async def user_auth_optional(
    token: Annotated[Optional[str], Depends(auth_optional)],
    db: Annotated[Session, Depends(get_db)],
) -> User | None:
    if not token:
        return None
    return await get_user_from_token(token, db)
