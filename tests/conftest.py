import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Profile, Article
from dependencies import get_db, create_access_token
from main import app


TEST_DATABASE_URL = "sqlite:///./test_db.sqlite"
engine = create_engine(TEST_DATABASE_URL)
TestSessionMaker = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestSessionMaker()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function")
def create_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


# @pytest.fixture(scope="function")
# def db_session(create_db):
#     connection = engine.connect()
#     transaction = connection.begin()
#     session = TestSessionMaker(bind=connection)
#     yield session
#     session.close()
#     transaction.rollback()
#     connection.close()


@pytest.fixture
def db_session(create_db):
    yield next(override_get_db())


@pytest.fixture(scope="function")
def test_user(db_session):
    user = User(
        email="user@email.com",
        password_hash="testpassword",
        username="user",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(scope="function")
def test_profile(db_session, test_user):
    profile_info = {
        "bio": "test user",
        "image": "https://url/to/image.jpg",
    }

    profile = Profile(**profile_info)
    profile.user_id = test_user.id
    db_session.add(profile)
    db_session.commit()
    return profile


@pytest.fixture(scope="function")
def test_article(db_session, test_profile):
    article_info = {
        "title": "Test Title",
        "description": "This is a test description",
        "body": "This is the body of my article",
    }
    article = Article(**article_info, profile_id=test_profile.id)
    db_session.add(article)
    db_session.commit()
    return article


@pytest.fixture(scope="function")
def test_token(create_db):
    user_details = {
        "username": "tokenuser",
        "email": "token@email.com",
        "password_hash": "pass",
    }
    db = next(override_get_db())
    user = User(**user_details)
    db.add(user)
    profile = Profile()
    user.profile = profile
    db.commit()
    payload = {
        "sub": user.id,
        "email": user.email,
        "username": user.username,
    }
    token = create_access_token(payload)
    db.close()
    return token


@pytest.fixture
def favorite_article():
    user_details = {
        "username": "fave",
        "email": "fave@email.com",
        "password_hash": "pass",
    }
    user = User(**user_details)
    pass
