import random
import string
import jwt
import pytest
from typing import Any
from fastapi import Response
from fastapi.testclient import TestClient

from models import User, Profile, Article, Tag, Comment
from schemas import articles
from dependencies import decode_token

from .conftest import client


def random_string(length=8):
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for _ in range(length))


def random_sentence(length=4):
    return " ".join(random_string(random.randint(1, 8)) for _ in range(length))


def get_article_details():
    while True:
        yield {
            "title": random_sentence(),
            "description": random_sentence(),
            "body": random_sentence(8),
            "tagList": [random_string() for _ in range(2)],
        }


def create_articles(token, *, number=3) -> list[tuple[dict[str, Any], Response]]:
    article_generator = get_article_details()
    articles = [next(article_generator) for _ in range(number)]
    result = []
    for article in articles:
        response = client.post(
            "/api/articles",
            headers={"Authorization": f"Bearer {token}"},
            json={"article": article},
        )
        result.append((article, response))
    return result


# @TODO test malformed input errors


def test_article_creation_works(test_token, db_session):
    article_details = next(get_article_details())
    response = client.post(
        "/api/articles",
        headers={"Authorization": f"Bearer {test_token}"},
        json={"article": article_details},
    )
    assert response.status_code == 200
    data = response.json()["article"]
    assert data["title"] == article_details["title"]
    article = db_session.query(Article).filter_by(slug=data["slug"]).first()
    assert article is not None
    article_schema = articles.ArticleOut.model_validate(
        article, from_attributes=True
    ).model_dump(by_alias=True, mode="json")
    assert data == article_schema


def test_get_list_of_articles(test_token, db_session):
    articles = create_articles(test_token)
    response = client.get("/api/articles")
    assert response.status_code == 200
    data = response.json()["articles"]
    assert len(data) == len(articles)


def test_get_list_of_articles_filtered_by_tag(test_token):
    article, _ = create_articles(test_token, number=2)[0]
    tag = article["tagList"][0]
    response = client.get(f"/api/articles?tag={tag}")
    assert response.status_code == 200
    data = response.json()["articles"]
    assert len(data) == 1
    assert tag in data[0]["tagList"]
    response = client.get(f"/api/articles?tag=idontexist")
    assert response.status_code == 200
    assert len(response.json()["articles"]) == 0


def test_get_list_of_articles_filtered_by_author(test_token):
    article, _ = create_articles(test_token, number=2)[0]
    author = decode_token(test_token).username
    response = client.get(f"/api/articles?author={author}")
    assert response.status_code == 200
    data = response.json()["articles"]
    assert len(data) == 2
    assert data[0]["author"]["username"] == author
    response = client.get("/api/articles?author=IdontExist")
    assert response.status_code == 404


def test_get_list_of_articles_filtered_by_favorited(
    test_token, test_user, test_profile, test_article, db_session
):
    test_user.profile = test_profile
    test_profile.favorites.append(test_article)
    db_session.commit()
    create_articles(test_token, number=2)
    response = client.get(f"/api/articles?favorited={test_profile.username}")
    assert response.status_code == 200
    data = response.json()["articles"]
    assert len(data) == 1
    assert data[0]["slug"] == test_article.slug
    response = client.get(f"/api/articles?favorited=IdontExist")
    assert response.status_code == 404


@pytest.mark.parametrize(
    "params, expected_length",
    [
        ({"limit": 3}, 3),  # limit is 3
        ({"offset": 3}, 2),  # offset is 3
        ({"offset": 0}, 5),  # offset is 0
        ({"limit": 0}, 0),  # limit is 0
    ],
)
def test_get_list_of_articles_with_limit_and_offset(
    test_token, params, expected_length
):
    create_articles(test_token, number=5)
    response = client.get("/api/articles", params=params)
    assert response.status_code == 200
    assert len(response.json()["articles"]) == expected_length


def test_get_single_article_using_slug(test_article, test_profile):
    slug = test_article.slug
    response = client.get(f"api/articles/{slug}")
    assert response.status_code == 200
    data = response.json()["article"]
    assert data["slug"] == slug
    assert data["title"] == test_article.title
    assert data["author"]["username"] == test_profile.username


def test_wrong_slug_on_getting_article_returns_404(test_article, test_token):
    response = client.get("api/articles/nonexistent")
    assert response.status_code == 404


def test_updating_article_using_slug(test_article, test_token, db_session):
    slug = test_article.slug
    updated_details = {
        "article": {
            "title": "this is my new title",
            "body": "three body problem",
            "description": "I defy description",
        },
    }
    response = client.put(
        f"/api/articles/{slug}",
        json=updated_details,
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    db_session.refresh(test_article)
    assert test_article.title == updated_details["article"]["title"]
    assert test_article.body == updated_details["article"]["body"]
    assert test_article.description == updated_details["article"]["description"]


def test_changing_slug_author_not_possible_during_update(
    test_token, test_article, db_session
):
    slug = test_article.slug
    updated_details = {
        "article": {"slug": "new_slug", "author": {"username": "newuser"}}
    }
    response = client.put(
        f"/api/articles/{slug}",
        json=updated_details,
        headers={"Authorization": f"Bearer {test_token}"},
    )
    db_session.refresh(test_article)
    assert test_article.slug != updated_details["article"]["slug"]
    assert (
        response.json()["article"]["author"]["username"]
        != updated_details["article"]["author"]["username"]
    )


def test_favoriting_article(test_token, test_article, db_session):
    slug = test_article.slug
    response = client.post(
        f"/api/articles/{slug}/favorite",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    assert response.json()["article"]["favorited"] == True
    user = (
        db_session.query(User)
        .filter_by(username=decode_token(test_token).username)
        .first()
    )
    assert test_article in user.profile.favorites


def test_unfavoriting_article(test_article, test_token, db_session):
    slug = test_article.slug
    response = client.delete(
        f"/api/articles/{slug}/favorite",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    assert response.json()["article"]["favorited"] == False
    user = (
        db_session.query(User)
        .filter_by(username=decode_token(test_token).username)
        .first()
    )
    assert test_article not in user.profile.favorites


def test_adding_comments_to_article(test_article, test_token, db_session):
    comment_body = {"comment": {"body": "to be or not to be"}}
    slug = test_article.slug
    response = client.post(
        f"/api/articles/{slug}/comments",
        json=comment_body,
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    comment = (
        db_session.query(Comment)
        .filter_by(body=comment_body["comment"]["body"])
        .first()
    )
    assert comment is not None
    db_session.refresh(test_article)
    assert comment in test_article.comments


def test_getting_article_comments(test_article, test_token, test_profile, db_session):
    slug = test_article.slug
    comments = [Comment(body=f"comment {x}") for x in range(3)]
    for comment in comments:
        comment.author = test_profile
    test_article.comments.extend(comments)
    db_session.commit()
    response = client.get(f"/api/articles/{slug}/comments")
    assert response.status_code == 200
    assert len(response.json()["comments"]) == 3


def test_deleting_comment_from_article(
    test_article, test_token, test_profile, db_session
):
    slug = test_article.slug
    comments = [Comment(body=f"comment {x}") for x in range(3)]
    for comment in comments:
        comment.author = test_profile
    test_article.comments.extend(comments)
    db_session.commit()
    comment_id = comments[0].id
    response = client.delete(
        f"/api/articles/{slug}/comments/{comment_id}",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    db_session.refresh(test_article)
    assert comments[0] not in test_article.comments


def test_deleting_article_succeeds(test_token, db_session):
    article_details = next(get_article_details())
    response = client.post(
        "/api/articles",
        headers={"Authorization": f"Bearer {test_token}"},
        json={"article": article_details},
    )
    slug = response.json()["article"]["slug"]
    response = client.delete(
        f"/api/articles/{slug}",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    article = db_session.query(Article).filter(Article.slug == slug).first()
    assert article is None


def test_getting_all_tags_succeeds(db_session):
    tag_names = ["random", "tag", "names"]
    tags = []
    for name in tag_names:
        tag = Tag(name=name)
        tags.append(tag)
        db_session.add(tag)
    db_session.commit()
    response = client.get("/api/tags")
    assert response.status_code == 200
    data = response.json()
    assert "tags" in data
    assert set(data["tags"]) == set(tag_names)


def test_following_is_set_correctly_when_getting_article_with_auth(
    db_session, test_article, test_token, test_profile
):
    slug = test_article.slug
    decoded_token = decode_token(test_token)
    token_user = db_session.get(User, decoded_token.user_id)
    test_profile.followers.append(token_user.profile)
    db_session.commit()
    db_session.refresh(test_profile)
    response = client.get(
        f"api/articles/{slug}", headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    assert response.json()["article"]["author"]["following"] == True


def test_getting_article_feed_works(db_session, test_token, test_profile):
    user_id = decode_token(test_token).user_id
    token_user = db_session.get(User, user_id)
    test_profile.followers.append(token_user.profile)
    for _ in range(3):
        article_details = next(get_article_details())
        article_details.pop("tagList")
        article = Article(**article_details)
        article.author = test_profile
        db_session.add(article)
    db_session.commit()
    response = client.get(
        "/api/articles/feed", headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    articles = response.json()["articles"]
    assert len(articles) == 3
    for article in articles:
        assert article["author"]["username"] == test_profile.user.username
        assert article["author"]["following"] == True


# @TODO: check that favorited and following status are set correctly on the relevant responses
