import uuid
from django.db import models
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    bio = models.TextField(blank=True)
    image = models.CharField(max_length=255)

    def __str__(self):
        return f'Profile: {self.user}'


class Article(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    description = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
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
    body = models.TextField
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)

    def __str__(self):
        return f'Comment: {self.body}'


class Follows(models.Model):
    initiator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followed_by')
    created_at = models.DateTimeField(auto_now_add=True)


class UserFavourite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class Tag(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return f'Tag: {self.name}'


class ArticleTag(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
