import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..models import Base, User, Profile, Article


TEST_DATABASE_URL = "sqlite:///./test_db.sqlite"
engine = create_engine(TEST_DATABASE_URL)
TestSessionMaker = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def create_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(create_db):
    connection = engine.connect()
    transaction = connection.begin()
    session = TestSessionMaker(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def test_user(db_session):
    user = User(email="user@email.com", password="testpassword")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(scope="function")
def test_profile(db_session, test_user):
    profile_info = {
        "username": "user",
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
