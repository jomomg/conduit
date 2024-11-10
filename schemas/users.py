from pydantic import BaseModel, ConfigDict
from typing import Optional


class UserLogin(BaseModel):
    email: str
    password: str


class UserRegister(UserLogin):
    username: str


class UserRegisterOut(BaseModel):
    email: str
    username: str
    model_config = ConfigDict(from_attributes=True)


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
