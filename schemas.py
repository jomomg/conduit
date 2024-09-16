from datetime import datetime
from pydantic import BaseModel


class BaseUser(BaseModel):
    email: str


class UserLogin(BaseUser):
    password: str


class UserRegistration(UserLogin):
    username: str


class UserOut(BaseUser):
    class Config:
        orm_mode = True


class Profile(BaseModel):
    username: str
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
