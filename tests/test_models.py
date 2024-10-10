from ..models import User, Profile, Article, Tag, Comment
from ..utils import slugify_title, generate_b64_uuid


def test_create_user(db_session, test_user):
    user = db_session.query(User).filter_by(email=test_user.email).first()
    assert user is not None
    assert user.email == test_user.email


def test_user_profile_rlnshp(db_session, test_user, test_profile):
    user = db_session.query(User).filter_by(email=test_user.email).first()
    assert user.profile == test_profile


def test_profile_following(db_session, test_profile):
    user1 = User(
        email="user1ew@email.com", password_hash="testpassword", username="user1"
    )
    user2 = User(
        email="user2@email.com", password_hash="testpassword", username="user2"
    )
    db_session.add_all([user1, user2])
    db_session.commit()
    profile1 = Profile(user_id=user1.id)
    profile2 = Profile(user_id=user2.id)
    db_session.add_all([profile1, profile2])
    db_session.commit()
    test_profile.follows.append(profile1)
    assert test_profile in profile1.followers
    profile2.followers.extend([profile1, test_profile])
    assert profile2 in profile1.follows
    assert profile2 in test_profile.follows


def test_create_article(db_session, test_profile, test_article):
    article = db_session.query(Article).filter_by(title="Test Title").first()
    assert article.title == test_article.title
    title_len = len(article.title)
    assert article.slug[:title_len] == slugify_title("Test Title")[:title_len]
    assert article.author == test_profile
    assert article.created_at is not None
    assert article.updated_at is None
    assert article in test_profile.articles
    article.title = "updated test title"
    db_session.commit()
    assert article.updated_at is not None


def test_favoriting_article(db_session, test_article, test_profile):
    test_profile.favorites.append(test_article)
    retrieved = db_session.query(Article).filter_by(title=test_article.title).first()
    assert test_profile in retrieved.favorited_by


def test_article_tags(db_session, test_article):
    tag1 = Tag(name="tag1")
    tag2 = Tag(name="tag2")
    db_session.add(tag1)
    db_session.add(tag2)
    db_session.commit()
    test_article.tags.extend([tag1, tag2])
    article = db_session.query(Article).filter_by(title="Test Title").first()
    assert article in tag1.articles
    assert article in tag2.articles


def test_article_comments(db_session, test_article, test_profile):
    comment = Comment(body="what a spicy comment")
    comment.article_id = test_article.id
    comment.profile_id = test_profile.id
    db_session.add(comment)
    db_session.commit()
    assert comment in test_article.comments
    assert comment.author == test_profile
    assert comment in test_profile.comments
    assert comment.created_at is not None
