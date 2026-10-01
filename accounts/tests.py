from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Follow, Profile

class AccountTests(TestCase):
    def test_registration_creates_profile_and_authenticates(self):
        response = self.client.post(reverse("register"), {"username": "newperson", "email": "NEW@example.com", "password1": "Safe-passphrase-942!", "password2": "Safe-passphrase-942!"})
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="newperson")
        self.assertTrue(user.check_password("Safe-passphrase-942!"))
        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_duplicate_email_rejected_case_insensitively(self):
        User.objects.create_user("existing", "person@example.com", "passphrase-12345")
        response = self.client.post(reverse("register"), {"username": "another", "email": "PERSON@example.com", "password1": "Safe-passphrase-942!", "password2": "Safe-passphrase-942!"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="another").exists())

    def test_login_and_logout(self):
        user = User.objects.create_user("member", password="passphrase-12345")
        response = self.client.post(reverse("login"), {"username": "member", "password": "passphrase-12345"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_invalid_login_is_rejected(self):
        User.objects.create_user("member", password="passphrase-12345")
        response = self.client.post(reverse("login"), {"username": "member", "password": "incorrect-password"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_profile_edit_is_owner_only(self):
        one = User.objects.create_user("one", password="passphrase-12345")
        two = User.objects.create_user("two", password="passphrase-12345")
        self.client.force_login(one)
        response = self.client.post(reverse("edit_profile"), {"bio": "My story"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Profile.objects.get(user=one).bio, "My story")
        self.assertEqual(self.client.get(reverse("profile", args=[two.username])).status_code, 200)

    def test_follow_duplicate_and_self_follow_are_prevented(self):
        one = User.objects.create_user("one", password="passphrase-12345")
        two = User.objects.create_user("two", password="passphrase-12345")
        self.client.force_login(one)
        url = reverse("toggle_follow", args=[two.username])
        self.assertEqual(self.client.post(url).json()["following"], True)
        self.assertEqual(self.client.post(url).json()["following"], False)
        self.assertEqual(Follow.objects.count(), 0)
        response = self.client.post(reverse("toggle_follow", args=[one.username]))
        self.assertEqual(response.status_code, 400)
        from django.db import IntegrityError, transaction
        with self.assertRaises(IntegrityError):
            with transaction.atomic(): Follow.objects.create(follower=one, following=one)

    def test_search_is_case_insensitive_and_empty_is_safe(self):
        User.objects.create_user("John_dev", password="passphrase-12345")
        self.assertContains(self.client.get(reverse("search"), {"q": "JOHN"}), "John_dev")
        self.assertEqual(self.client.get(reverse("search")).status_code, 200)
