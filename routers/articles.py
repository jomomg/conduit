from typing import Annotated, Optional, Callable
from functools import wraps
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from ..dependencies import get_db, get_current_active_user, user_auth_optional
from ..models import Article, User, Tag, Comment, Profile
from ..schemas.articles import (
    ArticleCreate,
    ArticleOut,
    ArticleUpdate,
    ListArticleOut,
    CommentIn,
    CommentOut,
    TagList,
)


router = APIRouter()

DatabaseDep = Annotated[Session, Depends(get_db)]
ActiveUserDep = Annotated[User, Depends(get_current_active_user)]
AuthOptionalDep = Annotated[Optional[User], Depends(user_auth_optional)]


def set_following_flag(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(*args, **kwargs):

        current_user = kwargs.get("current_user")
        ret_object = await func(*args, **kwargs)

        if not current_user:
            return ret_object

        def check_and_set_following(obj, profile):
            if profile in obj.followers:
                setattr(obj, "following", True)

        if isinstance(ret_object, Profile):
            check_and_set_following(ret_object, current_user.profile)
        if isinstance(ret_object, Article) or isinstance(ret_object, Comment):
            check_and_set_following(ret_object.author, current_user.profile)
        return ret_object

    return wrapper


def set_favorited_status(
    article: Article, current_profile: Profile | None = None
) -> Article:
    status = bool(current_profile) and article in current_profile.favorites
    setattr(article, "favorited", status)
    return article


def get_article_by_slug_or_404(db: Session, slug: str) -> Article:
    query = select(Article).where(Article.slug == slug)
    result = db.execute(query).scalar()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Article not found"
        )
    return result


def get_user_or_404(db: Session, username: str) -> User:
    statement = select(User).where(User.username == username)
    result = db.execute(statement).scalar()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return result


def find_or_create_tags(db: Session, tag_names: list[str]) -> list[Tag]:
    existing_tags = db.query(Tag).filter(Tag.name.in_(tag_names)).all()
    existing_tag_names = {tag.name for tag in existing_tags}
    tags_to_add = set(tag_names) - existing_tag_names
    new_tags = []
    if tags_to_add:
        for tag_name in tags_to_add:
            new_tag = Tag(name=tag_name)
            db.add(new_tag)
            new_tags.append(new_tag)
    return new_tags + existing_tags


@router.post("/articles", response_model=ArticleOut)
async def create_article(
    article_details: Annotated[ArticleCreate, Body(embed=True, alias="article")],
    current_user: ActiveUserDep,
    db: DatabaseDep,
):
    """Create a new article"""

    new_article = Article(
        title=article_details.title,
        body=article_details.body,
        description=article_details.description,
    )
    new_article.author = current_user.profile
    tags_to_add = find_or_create_tags(db, article_details.tagList)
    new_article.tags = tags_to_add
    db.add(new_article)
    db.commit()
    db.refresh(new_article)
    return new_article


@router.get(
    "/articles",
    response_model=list[ListArticleOut],
)
async def list_articles(
    db: DatabaseDep,
    offset: int = 0,
    limit: int = 20,
    tag: Optional[str] = None,
    author: Optional[str] = None,
    favorited: Optional[str] = None,
):
    """Retrieve multiple articles"""

    query = select(Article)
    user = None
    if tag:
        query = query.where(Article.tags.any(Tag.name == tag))
    if author:
        user = get_user_or_404(db, username=author)
        query = query.where(Article.author == user.profile)
    if favorited:
        user = get_user_or_404(db, username=favorited)
        query = query.join(Article.favorited_by).where(Profile.id == user.profile.id)
    query = query.order_by(desc(Article.created_at)).limit(limit).offset(offset)
    articles = [
        set_favorited_status(article) for article in db.execute(query).scalars()
    ]
    return articles


@router.get("/articles/{slug}", response_model=ArticleOut)
@set_following_flag
async def get_article(slug: str, db: DatabaseDep, current_user: AuthOptionalDep):
    """Retrieve a single article"""

    article = get_article_by_slug_or_404(db, slug=slug)
    return article


@router.put("/articles/{slug}", response_model=ArticleOut)
@set_following_flag
async def update_article(
    slug: str,
    article_details: Annotated[ArticleUpdate, Body(embed=True, alias="article")],
    db: DatabaseDep,
    current_user: ActiveUserDep,
):
    """Update/modify an articles details"""

    article = get_article_by_slug_or_404(db, slug=slug)
    for key, value in article_details.model_dump(exclude_unset=True).items():
        setattr(article, key, value)
    db.commit()
    db.refresh(article)
    article = set_favorited_status(article, current_user.profile)
    return article


@router.delete("/articles/{slug}")
async def delete_article(
    slug: str,
    db: DatabaseDep,
    _: ActiveUserDep,
):
    """Delete an article"""

    article = get_article_by_slug_or_404(db, slug=slug)
    db.delete(article)
    db.commit()
    return


@router.post("/articles/{slug}/favorite", response_model=ArticleOut)
@set_following_flag
async def favorite_article(
    slug: str,
    current_user: ActiveUserDep,
    db: DatabaseDep,
):
    """Favorite an article"""

    article = get_article_by_slug_or_404(db, slug=slug)
    favorites = current_user.profile.favorites
    if article not in favorites:
        favorites.append(article)
    db.commit()
    db.refresh(article)
    article = set_favorited_status(article, current_user.profile)
    return article


@router.delete("/articles/{slug}/favorite", response_model=ArticleOut)
@set_following_flag
async def unfavorite_article(
    slug: str,
    current_user: ActiveUserDep,
    db: DatabaseDep,
):
    """unfavorite an article"""

    article = get_article_by_slug_or_404(db, slug=slug)
    favorites = current_user.profile.favorites
    if article in favorites:
        favorites.remove(article)
    db.commit()
    return article


@router.post("/articles/{slug}/comments", response_model=CommentOut)
@set_following_flag
async def add_article_comment(
    slug: str,
    comment_details: Annotated[CommentIn, Body(embed=True, alias="comment")],
    current_user: ActiveUserDep,
    db: DatabaseDep,
):
    """Add a comment to an article"""

    new_comment = Comment(body=comment_details.body)
    article = get_article_by_slug_or_404(db, slug=slug)
    new_comment.author = current_user.profile
    new_comment.article = article
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment


@router.get("/articles/{slug}/comments", response_model=list[CommentOut])
async def get_article_comments(slug: str, db: DatabaseDep):
    """Get comments associated with an article"""

    article = get_article_by_slug_or_404(db, slug=slug)
    return article.comments


@router.delete("/articles/{slug}/comments/{comment_id}")
async def delete_article_comment(
    slug: str,
    comment_id: str,
    db: DatabaseDep,
    _: ActiveUserDep,
):
    """Delete comment from an article"""

    get_article_by_slug_or_404(db, slug=slug)
    query = select(Comment).where(Comment.id == comment_id)
    result = db.execute(query).scalar()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )
    db.delete(result)
    db.commit()
    return


@router.get("/tags", response_model=TagList)
def get_tags(db: DatabaseDep):
    """Return a list of tags"""

    tag_list_query = select(Tag)
    tag_list = db.execute(tag_list_query).scalars()
    return {"tags": [tag.name for tag in tag_list]}
