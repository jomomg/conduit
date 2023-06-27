import uuid
from django.db import models
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify


class UserProfile(User):
    """
    User Profile model. Extends the default Django User model
    """
    bio = models.TextField(blank=True)
    image = models.CharField(max_length=255, blank=True)


class Article(models.Model):
    """
    Article model. Stores all article information
    """
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    description = models.TextField(blank=True)
    author = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            unique_str = str(uuid.uuid4())[:8]
            self.slug = slugify(f'{self.title}-{unique_str}')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Article: {self.title}'


class Comment(models.Model):
    """
    Comment model. Stores information about comments
    """
    body = models.TextField
    author = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)

    def __str__(self):
        return f'Comment: {self.body}'


class Follows(models.Model):
    """
    Model used to track users following each other
    """
    initiator = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='following')
    recipient = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='followed_by')
    created_at = models.DateTimeField(auto_now_add=True)


class UserFavourites(models.Model):
    """
    Model used to track articles favourited by users
    """
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class Tag(models.Model):
    """
    Model for tracking tags
    """
    name = models.CharField(max_length=30)

    def __str__(self):
        return f'Tag: {self.name}'


class ArticleTags(models.Model):
    """
    Model for tags on articles
    """
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
