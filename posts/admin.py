from django.contrib import admin
from .models import Comment, Like, Post

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("author", "created_at", "updated_at")
    search_fields = ("author__username", "content")
    list_filter = ("created_at", "updated_at")
    ordering = ("-created_at",)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "post", "created_at")
    search_fields = ("author__username", "content")
    list_filter = ("created_at",)
    ordering = ("-created_at",)

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("user", "post", "created_at")
    search_fields = ("user__username", "post__content")
    list_filter = ("created_at",)
    ordering = ("-created_at",)
