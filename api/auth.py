import jwt
from rest_framework import authentication
from rest_framework import exceptions

import conduit.settings
from api.models import UserProfile

SECRET = conduit.settings.SECRET_KEY


class JWTAuthentication(authentication.TokenAuthentication):
    """
    JWT Authentication class. Modifies the standard rest framework TokenAuthentication
    class to use JWT tokens instead. Returns None if authentication fails or a tuple
    of (user, None) if successful.
    """
    keyword = 'Token'
    model = UserProfile

    def authenticate_credentials(self, token):
        try:
            decoded = jwt.decode(token, SECRET, algorithms='HS256')
        except jwt.exceptions.DecodeError:
            raise exceptions.AuthenticationFailed('Invalid token')
        except jwt.exceptions.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Expired token')
        except jwt.exceptions.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token')
        try:
            user = UserProfile.objects.get(email=decoded['email'])
        except UserProfile.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid token')
        return user, None
