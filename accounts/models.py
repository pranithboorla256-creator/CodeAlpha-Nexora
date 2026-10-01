from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField(upload_to="avatars/", blank=True, validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])])
    bio = models.CharField(max_length=280, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return f"Profile: {self.user.username}"

class Follow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following_links")
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="follower_links")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["follower", "following"], name="unique_follow_relationship"), models.CheckConstraint(condition=~models.Q(follower=models.F("following")), name="prevent_self_follow")]
        indexes = [models.Index(fields=["following", "-created_at"])]
        ordering = ["-created_at"]
    def __str__(self): return f"{self.follower} follows {self.following}"

class Notification(models.Model):
    FOLLOW = "follow"
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_notifications")
    kind = models.CharField(max_length=24, default=FOLLOW)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "is_read", "-created_at"])]

    def __str__(self):
        return f"{self.actor} → {self.recipient}: {self.kind}"
