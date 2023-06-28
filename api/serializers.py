import jwt
from rest_framework import serializers, exceptions

import conduit.settings
from api.models import Article, Comment, Tag, UserProfile

SECRET = conduit.settings.SECRET_KEY


class ArticleSerializer(serializers.ModelSerializer):
    pass


class CommentSerializer(serializers.ModelSerializer):
    pass


class TagSerializer(serializers.ModelSerializer):
    pass


class UserProfileSerializer(serializers.ModelSerializer):
    """
    User Profile Serializer
    """
    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'password', 'bio', 'image']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'bio': {'required': False},
            'image': {'required': False}
        }

    def create(self, validated_data):
        user = UserProfile(email=validated_data['email'], username=validated_data['username'])
        user.set_password(validated_data['password'])
        user.save()
        return user

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance

    def to_internal_value(self, data):
        errors = {}
        if 'user' not in data:
            errors['user'] = ['this field is required']
            raise serializers.ValidationError(errors)
        else:
            return super().to_internal_value(data['user'])


class LoginSerializer(serializers.ModelSerializer):
    token = serializers.CharField(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['email', 'password', 'token']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'write_only': True}
        }

    def to_internal_value(self, data):
        errors = {}
        if 'user' not in data:
            errors['user'] = ['this field is required']
            raise serializers.ValidationError(errors)
        else:
            return super().to_internal_value(data['user'])

    def validate(self, data):
        user = self.authenticate(email=data['email'], password=data['password'])
        print('-->', user)
        if not user:
            raise exceptions.AuthenticationFailed('Invalid username/password')
        else:
            data['token'] = self.generate_jwt_token(user)
        return data

    @staticmethod
    def authenticate(email, password):
        try:
            user = UserProfile.objects.get(email=email)
            if user.check_password(password):
                return user
            else:
                return False
        except UserProfile.DoesNotExist:
            return False

    @staticmethod
    def generate_jwt_token(user):
        payload = {
            'username': user.username,
            'email': user.email
        }
        token = jwt.encode(payload, SECRET, algorithm='HS256')
        return token
