from pydantic import BaseModel, ConfigDict
from typing import Optional


class BaseUserSchema(BaseModel):
    email: str


class UserLogin(BaseUserSchema):
    password: str


class UserRegisterIn(UserLogin):
    username: str


class UserRegisterOut(BaseUserSchema):
    username: str

    model_config = ConfigDict(from_attributes=True)


class UserOut(UserRegisterOut):
    bio: str | None = None
    image: str | None = None


class UserLoginOut(UserOut):
    token: str


class UserUpdate(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    bio: Optional[str] = None
    image: Optional[str] = None


class DecodedToken(BaseModel):
    user_id: str
    email: str
    username: str
