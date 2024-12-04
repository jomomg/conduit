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


# test access with expired token fails
# test access with invalid token fails


def test_user_registration_works(db_session):
    user_details = {
        "user": {"email": "new@user.com", "username": "newuser", "password": "pass"}
    }
    response = client.post("/api/users", json=user_details)
    assert response.status_code == 200
    return_data = response.json()["user"]
    assert "password" not in return_data
    assert "email" in return_data
    assert "username" in return_data
    user = (
        db_session.query(User)
        .filter(User.email == user_details["user"]["email"])
        .first()
    )
    assert user is not None
    assert user.profile is not None


def test_user_login_with_correct_credentials_works(db_session):
    user_details = {
        "user": {"email": "new@user.com", "username": "newuser", "password": "pass"}
    }
    register = client.post("/api/users", json=user_details)
    assert register.status_code == 200
    login = client.post("api/users/login", json=user_details)
    assert login.status_code == 200
    data = login.json()["user"]
    assert "token" in data
    assert "password" not in data


@pytest.mark.parametrize(
    "login_details",
    [
        {"email": "wrong@email.com", "password": "pass"},
        {"email": "new@user.com", "password": "wrongpass"},
    ],
)
def test_user_login_with_incorrect_credentials_fails(db_session, login_details):
    user_details = {"email": "new@user.com", "username": "newuser", "password": "pass"}
    error_detail = "Incorrect email or password"

    register = client.post("/api/users", json={"user": user_details})
    assert register.status_code == 200

    login = client.post("/api/users/login", json={"user": login_details})
    assert login.status_code == 401
    assert login.json()["detail"] == error_detail


def test_updating_user_details_works(test_token):
    new_details = {"user": {"email": "other@new.com", "username": "other"}}
    update = client.put(
        "/api/user", headers={"Authorization": f"Bearer {test_token}"}, json=new_details
    )
    assert update.status_code == 200
    data = update.json()["user"]
    assert data["email"] == new_details["user"]["email"]
    assert data["username"] == new_details["user"]["username"]
    assert "password" not in data


def test_updating_to_an_existing_username_fails(test_token, test_user, db_session):
    new_details = {"user": {"username": test_user.username}}
    update = client.put(
        "/api/user",
        headers={"Authorization": f"Bearer {test_token}"},
        json=new_details,
    )
    assert update.status_code == 400
    assert update.json()["detail"] == "Username already exists"


def test_updating_to_an_existing_email_fails(test_token, test_user, db_session):
    new_details = {"user": {"email": test_user.email}}
    update = client.put(
        "/api/user",
        headers={"Authorization": f"Bearer {test_token}"},
        json=new_details,
    )
    assert update.status_code == 400
    assert update.json()["detail"] == "Email already exists"


def test_getting_current_user_details_works(test_token, db_session):
    response = client.get(
        "/api/user", headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    decoded_token = decode_token(test_token)
    data = response.json()["user"]
    assert data["username"] == decoded_token.username
    assert data["email"] == decoded_token.email
