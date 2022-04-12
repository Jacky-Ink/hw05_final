from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Flash')
        cls.group = Group.objects.create(
            title='test',
            slug='test_slug',
            description='test',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='test',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей Post и Group
        корректно работает __str__.
        """
        post = PostModelTests.post
        expected_post_str = post.text[:15]
        self.assertEqual(expected_post_str, str(post))

        group = PostModelTests.group
        expected_group_str = group.title
        self.assertEqual(expected_group_str, str(group))

    def test_post_verbose_name(self):
        """verbose_name в полях модели Post совпадает с ожидаемым."""
        post = PostModelTests.post
        field_verbose = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verbose.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_post_help_text(self):
        """help_text в полях модели Post совпадает с ожидаемым."""
        post = PostModelTests.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)
