from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from accounts.models import Follow, Notification
from .models import Comment, Like, Post

class SocialFeaturesTests(TestCase):
    def setUp(self):
        self.one = User.objects.create_user("one", password="passphrase-12345")
        self.two = User.objects.create_user("two", password="passphrase-12345")
        self.other = User.objects.create_user("other", password="passphrase-12345")
        self.post = Post.objects.create(author=self.one, content="Hello community")

    def test_create_edit_delete_own_post_and_reject_other_owner(self):
        self.client.force_login(self.one)
        response = self.client.post(reverse("create_post"), {"content": " A new post "})
        self.assertEqual(response.status_code, 302)
        created = Post.objects.get(content="A new post")
        self.assertEqual(created.author, self.one)
        self.assertEqual(self.client.post(reverse("edit_post", args=[created.pk]), {"content": "Edited"}).status_code, 302)
        self.client.force_login(self.two)
        self.assertEqual(self.client.get(reverse("edit_post", args=[created.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("delete_post", args=[created.pk])).status_code, 404)
        self.client.force_login(self.one)
        self.assertEqual(self.client.post(reverse("delete_post", args=[created.pk])).status_code, 302)
        self.assertFalse(Post.objects.filter(pk=created.pk).exists())

    def test_empty_post_rejected(self):
        self.client.force_login(self.one)
        self.client.post(reverse("create_post"), {"content": "    "})
        self.assertFalse(Post.objects.filter(content="").exists())

    def test_like_toggle_and_database_duplicate_constraint(self):
        self.client.force_login(self.two)
        url = reverse("toggle_like", args=[self.post.pk])
        self.assertEqual(self.client.post(url).json(), {"liked": True, "count": 1})
        self.assertEqual(self.client.post(url).json(), {"liked": False, "count": 0})
        Like.objects.create(user=self.two, post=self.post)
        from django.db import IntegrityError, transaction
        with self.assertRaises(IntegrityError):
            with transaction.atomic(): Like.objects.create(user=self.two, post=self.post)

    def test_comments_create_delete_permissions(self):
        self.client.force_login(self.two)
        self.client.post(reverse("add_comment", args=[self.post.pk]), {"content": "Nice post"})
        comment = Comment.objects.get()
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(reverse("delete_comment", args=[comment.pk])).status_code, 404)
        self.client.force_login(self.two)
        self.assertEqual(self.client.post(reverse("delete_comment", args=[comment.pk])).status_code, 302)
        self.assertFalse(Comment.objects.exists())

    def test_feed_includes_own_and_followed_not_unfollowed(self):
        followed_post = Post.objects.create(author=self.two, content="Followed content")
        Post.objects.create(author=self.other, content="Unfollowed content")
        Follow.objects.create(follower=self.one, following=self.two)
        self.client.force_login(self.one)
        response = self.client.get(reverse("feed"))
        self.assertContains(response, "Hello community")
        self.assertContains(response, "Followed content")
        self.assertNotContains(response, "Unfollowed content")

    def test_feed_is_paginated(self):
        for index in range(12): Post.objects.create(author=self.one, content=f"Post number {index}")
        self.client.force_login(self.one)
        response = self.client.get(reverse("feed"))
        self.assertTrue(response.context["page_obj"].has_next())
        self.assertEqual(response.context["page_obj"].paginator.per_page, 10)

    def test_feed_filters_following_and_own_posts(self):
        followed_post = Post.objects.create(author=self.two, content="Only in following")
        Follow.objects.create(follower=self.one, following=self.two)
        self.client.force_login(self.one)
        mine = self.client.get(reverse("feed"), {"filter": "mine"})
        self.assertContains(mine, "Hello community")
        self.assertNotContains(mine, "Only in following")
        following = self.client.get(reverse("feed"), {"filter": "following"})
        self.assertContains(following, "Only in following")
        self.assertNotContains(following, "Hello community")

    def test_new_follow_notifies_recipient_and_activity_marks_read(self):
        self.client.force_login(self.two)
        response = self.client.post(reverse("toggle_follow", args=[self.one.username]))
        self.assertEqual(response.json()["following"], True)
        notification = Notification.objects.get(recipient=self.one, actor=self.two)
        self.assertFalse(notification.is_read)
        self.client.force_login(self.one)
        response = self.client.get(reverse("notifications"))
        self.assertContains(response, "wants to connect with you")
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
        self.assertEqual(self.client.get(reverse("notifications")).status_code, 200)
