import random
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Table, func, select, ForeignKey, Column
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    validates,
)
from slugify import slugify

from .database import engine, SessionMaker
from .utils import slugify_title, generate_b64_uuid


def utcnow():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(primary_key=True, default=generate_b64_uuid)
    email: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]
    username: Mapped[str]
    profile: Mapped["Profile"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email})"


article_tags = Table(
    "article_tags",
    Base.metadata,
    Column("article_id", ForeignKey("articles.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)

profile_favorites = Table(
    "profile_favorites",
    Base.metadata,
    Column("profile_id", ForeignKey("profiles.id"), primary_key=True),
    Column("article_id", ForeignKey("articles.id"), primary_key=True),
)

profile_follows = Table(
    "profile_follows",
    Base.metadata,
    Column("following_id", ForeignKey("profiles.id"), primary_key=True),
    Column("follower_id", ForeignKey("profiles.id"), primary_key=True),
)


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(primary_key=True, default=generate_b64_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)

    bio: Mapped[Optional[str]]
    image: Mapped[Optional[str]]

    user: Mapped["User"] = relationship(back_populates="profile")
    articles: Mapped[list["Article"]] = relationship(back_populates="author")
    comments: Mapped[list["Comment"]] = relationship(back_populates="author")
    favorites: Mapped[list["Article"]] = relationship(
        secondary=profile_favorites, back_populates="favorited_by"
    )

    following: Mapped[list["Profile"]] = relationship(
        secondary=profile_follows,
        primaryjoin=id == profile_follows.c.follower_id,
        secondaryjoin=id == profile_follows.c.following_id,
        back_populates="followers",
    )
    followers: Mapped[list["Profile"]] = relationship(
        secondary=profile_follows,
        primaryjoin=id == profile_follows.c.following_id,
        secondaryjoin=id == profile_follows.c.follower_id,
        back_populates="following",
    )

    def __repr__(self) -> str:
        return f"Profile(username={self.username})"


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[str] = mapped_column(primary_key=True, default=generate_b64_uuid)
    title: Mapped[str] = mapped_column(String(300))
    slug: Mapped[str]
    profile_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"))
    description: Mapped[Optional[str]]
    body: Mapped[Optional[str]]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=func.now())
    comments: Mapped[list["Comment"]] = relationship(back_populates="article")
    author: Mapped["Profile"] = relationship(back_populates="articles")
    tags: Mapped[list["Tag"]] = relationship(
        secondary=article_tags, back_populates="articles"
    )
    favorited_by: Mapped[list[Profile]] = relationship(
        secondary=profile_favorites, back_populates="favorites"
    )

    def __repr__(self) -> str:
        return f"Article(id={self.id!r}, title={self.title!r})"

    @validates("title")
    def generate_slug(self, key, value):
        self.slug = slugify_title(value)
        return value


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(primary_key=True, default=generate_b64_uuid)
    name: Mapped[str] = mapped_column(unique=True)
    articles: Mapped[list["Article"]] = relationship(
        secondary=article_tags, back_populates="tags"
    )


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[str] = mapped_column(primary_key=True, default=generate_b64_uuid)
    profile_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"))
    article_id: Mapped[str] = mapped_column(ForeignKey("articles.id"))
    body: Mapped[str]
    article: Mapped["Article"] = relationship(back_populates="comments")
    author: Mapped["Profile"] = relationship(back_populates="comments")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=func.now())
