from datetime import datetime
from pydantic import BaseModel
from typing import Optional

# registration
# email, username, password


class BaseUserSchema(BaseModel):
    email: str


class UserLogin(BaseUserSchema):
    password: str


class UserRegisterIn(UserLogin):
    username: str


class UserRegisterOut(BaseUserSchema):
    username: str

    class Config:
        orm_mode = True


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


class Profile(BaseModel):
    bio: str
    image: str


class Tag(BaseModel):
    name: str


class BaseArticle(BaseModel):
    title: str
    description: str | None = None
    body: str | None = None
    tag_list: list[Tag] | None = []


class ArticleIn(BaseArticle):
    pass


class ArticleOut(BaseArticle):
    id: int
    created_at: datetime
    updated_at: datetime
    author: Profile
    favorited: bool
    favorites_count: int
    tag_list: list[Tag]


class Comment(BaseModel):
    pass
