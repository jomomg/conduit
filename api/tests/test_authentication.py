import pytest
from django.urls import reverse

USER_PAYLOAD = {
    'user': {
        'username': 'test',
        'email': 'test@example.com',
        'password': 'password1234'}
}


@pytest.mark.django_db
def test_user_registration_is_successful(api_client):
    url = reverse('user_registration')
    response = api_client.post(url, USER_PAYLOAD, format='json')
    assert response.status_code == 201
    assert 'password' not in response.json()
