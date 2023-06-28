from django.urls import path
from api import views


urlpatterns = [
    path('users', views.UserRegistration.as_view(), name='user_registration'),  # registration (POST)
    path('users/login', views.UserLogin.as_view(), name='user_login'),  # login (POST)
    # path('user'),         # get current user (GET, PUT)
    # path('profiles/<str:username>'),  # get user profile (GET)
    # path('profiles/<str:username>/follow'),  # follow user (POST, DELETE)
    # path('articles'),  # list and create articles (GET, POST)
    # path('articles/feed'),  # article feed (return articles by followed users, most recent first) (GET)
    # path('articles/<str:slug>'),  # single article (GET, PUT, DELETE)
    # path('articles/<str:slug>/comments'),  # article comments (GET, POST)
    # path('articles/<str:slug>/comments/<int:pk>'),  # single comment (GET, DELETE)
    # path('articles/<str:slug>/favorite'),  # favorite article (POST, DELETE)
    # path('tags')  # get tags (GET)
]
