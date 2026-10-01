from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("search/", views.search_users, name="search"),
    path("notifications/", views.notifications, name="notifications"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("profile/<str:username>/", views.profile_detail, name="profile"),
    path("profile/<str:username>/followers/", views.relationships, {"kind": "followers"}, name="followers"),
    path("profile/<str:username>/following/", views.relationships, {"kind": "following"}, name="following"),
]
