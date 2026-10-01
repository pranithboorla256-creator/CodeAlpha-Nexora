from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from .forms import ProfileForm, RegistrationForm
from .models import Follow, Notification, Profile
from posts.models import Post

def register(request):
    if request.user.is_authenticated: return redirect("feed")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Welcome to Nexora!")
        return redirect("feed")
    return render(request, "accounts/register.html", {"form": form})

def search_users(request):
    query = request.GET.get("q", "").strip()[:80]
    users = User.objects.none()
    if query: users = User.objects.filter(username__icontains=query, is_active=True).select_related("profile").order_by("username")[:50]
    following_ids = list(Follow.objects.filter(follower=request.user).values_list("following_id", flat=True)) if request.user.is_authenticated else []
    return render(request, "accounts/search.html", {"query": query, "users": users, "following_ids": following_ids})

def profile_detail(request, username):
    person = get_object_or_404(User.objects.select_related("profile"), username=username, is_active=True)
    Profile.objects.get_or_create(user=person)
    posts = Post.objects.filter(author=person).select_related("author", "author__profile").prefetch_related("likes", "comments__author", "comments__author__profile").order_by("-created_at")
    page = Paginator(posts, 10).get_page(request.GET.get("page"))
    is_following = request.user.is_authenticated and Follow.objects.filter(follower=request.user, following=person).exists()
    return render(request, "accounts/profile.html", {"person": person, "page_obj": page, "is_following": is_following})

@login_required
def edit_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile has been updated.")
        return redirect("profile", username=request.user.username)
    return render(request, "accounts/edit_profile.html", {"form": form})

def relationships(request, username, kind):
    person = get_object_or_404(User.objects.select_related("profile"), username=username, is_active=True)
    if kind == "followers": users = User.objects.filter(following_links__following=person, is_active=True).select_related("profile").order_by("username")
    else: users = User.objects.filter(following_links__follower=person, is_active=True).select_related("profile").order_by("username")
    following_ids = list(Follow.objects.filter(follower=request.user).values_list("following_id", flat=True)) if request.user.is_authenticated else []
    return render(request, "accounts/relationships.html", {"person": person, "kind": kind, "users": users, "following_ids": following_ids})

@login_required
def notifications(request):
    items = Notification.objects.filter(recipient=request.user).select_related("actor", "actor__profile")
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return render(request, "accounts/notifications.html", {"notifications": items[:50]})
