import random
import string
import jwt
import pytest
from typing import Any
from fastapi import Response
from fastapi.testclient import TestClient

from ..models import User, Profile, Article, Tag, Comment
from ..schemas import articles
from ..dependencies import decode_token

from .conftest import client


def get_user_from_token(db, token: str) -> User:
    decoded = decode_token(token)
    user = db.get(User, decoded.user_id)
    return user


def test_getting_a_profile_succeeds(db_session, test_profile):
    username = test_profile.username
    response = client.get(f"/api/profiles/{username}")
    assert response.status_code == 200
    assert "profile" in response.json()
    profile = response.json()["profile"]
    assert profile["username"] == test_profile.username
    assert profile["following"] == False
    assert {"bio", "image"}.issubset(profile.keys())


def test_following_status_is_set_correctly_when_authenticated(
    db_session, test_profile, test_token
):
    username = test_profile.username
    user = get_user_from_token(db_session, test_token)
    test_profile.followers.append(user.profile)
    db_session.commit()
    db_session.refresh(test_profile)
    response = client.get(f"/api/profiles/{username}")
    assert response.status_code == 200
    assert response.json()["profile"]["following"] == True


def test_getting_with_incorrect_username_returns_404(db_session, test_profile):
    response = client.get("/api/profiles/idontexist")
    assert response.status_code == 404


def test_following_a_profile_succeeds(db_session, test_profile, test_token):
    username = test_profile.username
    response = client.post(
        f"/api/profiles/{username}/follow",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    user = get_user_from_token(db_session, test_token)
    assert user.profile in test_profile.followers
    assert response.json()["profile"]["following"] == True


def test_unfollowing_a_profile_succeeds(db_session, test_profile, test_token):
    username = test_profile.username
    response = client.delete(
        f"/api/profiles/{username}/follow",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    user = get_user_from_token(db_session, test_token)
    assert user.profile not in test_profile.followers
    assert response.json()["profile"]["following"] == False
