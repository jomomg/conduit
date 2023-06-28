from django.contrib.auth.models import User
from rest_framework import serializers
from api.models import Article, Comment, Tag, UserProfile


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
