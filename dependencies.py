import jwt
from typing import Generator
from sqlalchemy.orm import Session
from .database import SessionMaker
from jwt.exceptions import InvalidTokenError
from typing import Annotated
from datetime import datetime, timezone, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .models import User
from .schemas import DecodedToken

TOKEN_EXPIRY_MINUTES = 120
SECRET_KEY = "TCEMfX9afLhjSPWHAhiipe2qfUxXW9OuQeWOXZKkGyBErBcFJJ"  # TODO move to .env
JWT_ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")


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


def create_access_token(token_payload: dict) -> str:
    payload = token_payload.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
    payload.update({"exp": expire})
    jwt_token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    return jwt_token


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
