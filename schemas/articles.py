from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from typing import Optional
from datetime import datetime


class Profile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    image: Optional[str]
    bio: Optional[str]
    following: bool = False


class ListArticleOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, alias_generator=to_camel, populate_by_name=True
    )

    slug: str
    title: str
    description: str
    created_at: datetime
    updated_at: Optional[datetime]
    favorited: bool = False
    favorites_count: int
    author: Profile
    tag_list: Optional[list[str]]


class ArticleOut(ListArticleOut):
    model_config = ConfigDict(
        from_attributes=True, alias_generator=to_camel, populate_by_name=True
    )
    body: str


class ArticleCreate(BaseModel):
    title: str
    description: str
    body: str
    tagList: list[str] = []


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    body: Optional[str] = None


class CommentIn(BaseModel):
    body: str


class CommentOut(CommentIn):
    model_config = ConfigDict(
        from_attributes=True, alias_generator=to_camel, populate_by_name=True
    )

    id: str
    created_at: datetime
    updated_at: Optional[datetime]
    author: Profile


class TagList(BaseModel):
    tags: list[str]
