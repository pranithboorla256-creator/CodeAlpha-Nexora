from django.contrib import admin
from .models import Follow, Notification, Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "updated_at")
    search_fields = ("user__username", "user__email", "bio")
    ordering = ("user__username",)

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "following", "created_at")
    search_fields = ("follower__username", "following__username")
    list_filter = ("created_at",)
    ordering = ("-created_at",)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "actor", "kind", "is_read", "created_at")
    search_fields = ("recipient__username", "actor__username")
    list_filter = ("kind", "is_read", "created_at")
    ordering = ("-created_at",)
