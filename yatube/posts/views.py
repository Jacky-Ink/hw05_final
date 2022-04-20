from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Post, Group, User

User = get_user_model()

NUMBER_OF_POSTS = 10


def paginator_of_page(request, posts):
    """Модуль отвечающий за разбитие текта на страницы."""
    paginator = Paginator(posts, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request: HttpRequest) -> HttpResponse:
    """Модуль отвечающий за главную страницу."""
    post_list = Post.objects.all()
    page_obj = paginator_of_page(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request: HttpRequest, slug) -> HttpResponse:
    """Модуль отвечающий за страницу сообщества."""
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.filter(group=group)
    page_obj = paginator_of_page(request, post_list)
    context = {
        'group': group,
        'post_list': post_list,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request: HttpRequest, username) -> HttpResponse:
    """Модуль отвечающий за личную страницу."""
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=author)
    posts_count = posts.count()
    page_obj = paginator_of_page(request, posts)
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author
    ).exists
    context = {
        'posts_count': posts_count,
        'author': author,
        'page_obj': page_obj,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request: HttpRequest, post_id) -> HttpResponse:
    """Модуль отвечающий за просмотр отдельного поста."""
    post = get_object_or_404(Post, id=post_id)
    comment_form = CommentForm(request.POST or None)
    comments = post.comments.all()
    count_of_posts = post.author.posts.all().count()
    title = f'Пост {post.text[:30]}'
    context = {
        'title': title,
        'count_of_posts': count_of_posts,
        'post': post,
        'post_id': post_id,
        'comment_form': comment_form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request: HttpRequest) -> HttpResponse:
    """Модуль отвечающий за страницу создания текста постов."""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user)
    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request: HttpRequest, post_id) -> HttpResponse:
    """Модуль отвечающий за страницу создания текста постов."""
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post.pk)
    context = {
        'form': form,
        'post_id': post_id,
        'is_edit': True
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request: HttpRequest, post_id) -> HttpResponse:
    """Модуль отвечающий за комментирование постов."""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request: HttpRequest) -> HttpResponse:
    """Модуль отвечающий за подписку."""
    following = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator_of_page(request, following)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request: HttpRequest, username) -> HttpResponse:
    """Модуль отвечающий за подписку на автора."""
    author = get_object_or_404(User, username=username)
    user = request.user
    if user != author:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request: HttpRequest, username) -> HttpResponse:
    """Модуль отвечающий за отписку от автора."""
    author = get_object_or_404(User, username=username)
    user = request.user
    if user != author:
        Follow.objects.filter(
            user=request.user,
            author__username=username
        ).delete()
    return redirect('posts:profile', username=username)
