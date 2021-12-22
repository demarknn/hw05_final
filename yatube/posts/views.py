from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Follow, Group, Post
from .models import User


def paginator(post_list, request):
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


@cache_page(1, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all().order_by('-pub_date')
    page_obj = paginator(post_list, request)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all().order_by('-pub_date')
    page_obj = paginator(posts, request)
    context = {
        'group': group,
        'posts': posts,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    page_obj = paginator(post_list, request)
    count = author.posts.all().count()
    context = {
        'author': author,
        'count': count,
        'page_obj': page_obj,
        'following': None,
    }
    if request.user.is_authenticated and request.user != author:
        following = (
            Follow.objects.filter(
                user=request.user).filter(author=author).exists()
        )
        context['following'] = following
        return render(request, 'posts/profile.html', context)
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    count = post.author.posts.all().count()
    comment_form = CommentForm()
    comments = post.comments.all().filter(post=post_id)
    context = {
        'count': count,
        'post': post,
        'comments': comments,
        'form': comment_form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    author = request.user
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = author
        new_post.save()
        return redirect('posts:profile', author)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    instance = get_object_or_404(Post, id=post_id)
    if instance.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=instance
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'is_edit': True,
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator(post_list, request)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    # Подписаться на автора
    author = get_object_or_404(User, username=username)
    user = request.user
    following = (
        Follow.objects.filter(
            user=request.user).filter(author=author).exists()
    )
    if request.user.is_authenticated and (
        request.user != author and following is False
    ):
        Follow.objects.get_or_create(user=user, author=author)
        return redirect('posts:profile', username=author)
    return redirect('users:login')


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    author = get_object_or_404(User, username=username)
    user = request.user
    Follow.objects.filter(user=user, author=author).delete()
    return redirect('posts:profile', username=author)
