from django.urls import path
from . import views

urlpatterns = [
    path("", views.feed, name="feed"),
    path("posts/create/", views.create_post, name="create_post"),
    path("posts/<int:pk>/edit/", views.edit_post, name="edit_post"),
    path("posts/<int:pk>/delete/", views.delete_post, name="delete_post"),
    path("posts/<int:pk>/like/", views.toggle_like, name="toggle_like"),
    path("posts/<int:pk>/comment/", views.add_comment, name="add_comment"),
    path("comments/<int:pk>/delete/", views.delete_comment, name="delete_comment"),
    path("users/<str:username>/follow/", views.toggle_follow, name="toggle_follow"),
]
