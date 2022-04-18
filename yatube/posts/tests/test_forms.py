from http import HTTPStatus

import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User, Comment

USERNAME = 'user_author'
USERNAME_ANOTHER = 'another_user'
TITLE = 'Наименование группы'
SLUG = 'text-slug'
DESCRIPTION = 'Текстовое описание'
TEXT = 'Тестовый текст'
NEW_TEXT = 'Новый текст'
CHANGE_TEXT = 'Измененный пост'
COMMENT_TEXT = 'Текст комментария'
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности адреса task/test-slug/
        cls.user_author = User.objects.create_user(USERNAME)
        cls.another_user = User.objects.create_user(USERNAME_ANOTHER)
        cls.group = Group.objects.create(
            title=TITLE,
            slug=SLUG,
            description=DESCRIPTION,
        )
        cls.post = Post.objects.create(
            text=TEXT,
            author=cls.user_author,
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user_author,
            text=COMMENT_TEXT
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем второй клиент
        self.authorized_client = Client()
        # Создаем трейтий клиент
        self.author_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.another_user)
        # Автор поста
        self.author_client.force_login(self.user_author)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        # Подсчитаем количество записей в Post
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Новый текст',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.another_user.username}),
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что создалась запись с нашим слагом
        self.assertTrue(
            Post.objects.filter(
                text=NEW_TEXT,
                group=self.group.id,
                image='posts/small.gif'
            ).exists()
        )

    def test_post_edit(self):
        """Валидная форма редактирует запись."""
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='big.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Измененный пост',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.author_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}),
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count)
        # Проверяем, что создалась запись с нашим слагом
        self.assertTrue(
            Post.objects.filter(
                text=CHANGE_TEXT,
                group=self.group,
                image='posts/big.gif'
            ).exists()
        )

    def test_create_comment(self):
        """Валидная форма создает запись в Comment."""
        comment_count = Comment.objects.count()
        form_data = {
            'post': self.post,
            'author': self.authorized_client,
            'text': COMMENT_TEXT,
        }
        response_comment = self.authorized_client.get(
            reverse('posts:add_comment', kwargs={
                'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response_comment, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}),
        )
        self.assertEqual(Comment.objects.count(), comment_count)
        self.assertTrue(
            Comment.objects.filter(
                post=self.post,
                author=self.user_author,
                text=COMMENT_TEXT
            ).exists()
        )

    def test_create_post_guest_client(self):
        """Проверяем, создания поста неавторизованным пользователем."""
        response_create = self.guest_client.post(reverse('posts:post_create'))
        self.assertEqual(response_create.status_code, HTTPStatus.FOUND)

    def test_create_comment_guest_client(self):
        comment_count = Comment.objects.count()
        form_data = {
            'post': self.post,
            'author': self.guest_client,
            'text': COMMENT_TEXT,
        }
        self.guest_client.post(reverse(
            'posts:add_comment',
            kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        response_redirect = self.guest_client.post(reverse(
            'posts:add_comment',
            kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Comment.objects.count(), comment_count)
        self.assertEqual(response_redirect.status_code, HTTPStatus.FOUND)
