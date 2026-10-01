import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, Exists, OuterRef, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from accounts.models import Follow, Notification
from .forms import CommentForm, PostForm
from .models import Comment, Like, Post

def feed(request):
    feed_filter = request.GET.get("filter", "for-you")
    if feed_filter not in {"for-you", "following", "mine"}:
        feed_filter = "for-you"
    following = Follow.objects.filter(follower=request.user).values_list("following_id", flat=True) if request.user.is_authenticated else []
    if request.user.is_authenticated and feed_filter == "following":
        posts = Post.objects.filter(author_id__in=following)
    elif request.user.is_authenticated and feed_filter == "mine":
        posts = Post.objects.filter(author=request.user)
    elif request.user.is_authenticated:
        posts = Post.objects.filter(Q(author=request.user) | Q(author_id__in=following))
    else:
        posts = Post.objects.all()
    posts = posts.select_related("author", "author__profile").annotate(like_count=Count("likes", distinct=True), comment_count=Count("comments", distinct=True)).order_by("-created_at", "-pk")
    if request.user.is_authenticated:
        posts = posts.annotate(user_liked=Exists(Like.objects.filter(post=OuterRef("pk"), user=request.user))).prefetch_related("comments__author", "comments__author__profile")
    else: posts = posts.prefetch_related("comments__author", "comments__author__profile")
    page = Paginator(posts, 10).get_page(request.GET.get("page"))
    suggestions = User.objects.filter(is_active=True).select_related("profile").exclude(pk__in=following)
    if request.user.is_authenticated:
        suggestions = suggestions.exclude(pk=request.user.pk)
    suggestions = suggestions.order_by("-date_joined")[:4]
    return render(request, "posts/feed.html", {"page_obj": page, "post_form": PostForm(), "people_to_follow": suggestions, "feed_filter": feed_filter})

@login_required
def create_post(request):
    if request.method != "POST": return redirect("feed")
    form = PostForm(request.POST)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        messages.success(request, "Your post is live.")
    else: messages.error(request, "Please enter a post with no more than 1,000 characters.")
    return redirect("feed")

@login_required
def edit_post(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)
    form = PostForm(request.POST or None, instance=post)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Post updated.")
        return redirect("profile", username=request.user.username)
    return render(request, "posts/edit_post.html", {"form": form, "post": post})

@login_required
@require_POST
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)
    post.delete()
    messages.success(request, "Post deleted.")
    return redirect("feed") if request.POST.get("next") == "feed" else redirect("profile", username=request.user.username)

@login_required
@require_POST
def toggle_like(request, pk):
    post = get_object_or_404(Post, pk=pk)
    existing = Like.objects.filter(user=request.user, post=post)
    if existing.exists(): existing.delete(); liked = False
    else:
        try:
            with transaction.atomic(): Like.objects.get_or_create(user=request.user, post=post)
            liked = True
        except IntegrityError: liked = True
    return JsonResponse({"liked": liked, "count": post.likes.count()})

@login_required
@require_POST
def toggle_follow(request, username):
    from django.contrib.auth.models import User
    target = get_object_or_404(User, username=username, is_active=True)
    if target == request.user: return JsonResponse({"error": "You cannot follow yourself."}, status=400)
    relation, created = Follow.objects.get_or_create(follower=request.user, following=target)
    if created:
        Notification.objects.create(recipient=target, actor=request.user, kind=Notification.FOLLOW)
    else:
        relation.delete()
    return JsonResponse({"following": created, "count": target.follower_links.count()})

@login_required
@require_POST
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author, comment.post = request.user, post
        comment.save()
        messages.success(request, "Comment added.")
    else: messages.error(request, "Please enter a comment of up to 500 characters.")
    return redirect("feed")

@login_required
@require_POST
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk, author=request.user)
    post_author = comment.post.author.username
    comment.delete()
    messages.success(request, "Comment deleted.")
    return redirect("feed") if request.POST.get("next") == "feed" else redirect("profile", username=post_author)
