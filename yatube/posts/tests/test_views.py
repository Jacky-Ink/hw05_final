from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from ..forms import PostForm
from ..models import Group, Post

User = get_user_model()


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create_user(username='BatMan')
        cls.user_2 = User.objects.create_user(username='Flash')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Описание тестовой группы',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug_2',
            description='Описание тестовой группы 2',
        )
        cls.post_1 = Post.objects.create(
            author=cls.user_1,
            text='Тестовый пост 1',
            pub_date='01.04.2022',
            group_id=cls.group.id
        )
        cls.post_2 = Post.objects.create(
            author=cls.user_2,
            text='Тестовый пост 2',
            pub_date='02.04.2022',
            group_id=cls.group_2.id,
        )
        cls.form_data = {
            'text': 'Новый пост',
            'group': cls.group.id,
            'author': cls.post_1.author
        }
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        cls.name_page_list = [
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': cls.post_1.author}
            ),
        ]

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.user_1)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        name_page_template = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}
                    ): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.post_1.author}
                    ): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post_1.id}
                    ): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post_1.id}
                    ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in name_page_template.items():
            with self.subTest(template=template):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_correct_context(self):
        """Шаблон index формируется со всеми постами из БД."""
        response = self.author_client.get(reverse('posts:index'))
        object_post_list = response.context['page_obj'].object_list
        self.assertTrue(self.post_1 in object_post_list)
        self.assertTrue(self.post_2 in object_post_list)

    def test_group_posts_correct_context(self):
        """Шаблон group_posts формируется с постами
        отфильтрованными по группе.
        """
        response = self.author_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}
                    )
        )
        object_page_obj = response.context['page_obj']
        self.assertEqual(
            object_page_obj.object_list[0].group,
            self.group)
        self.assertEqual(len(object_page_obj.object_list), 1)

    def test_profile_correct_context(self):
        """Шаблон profile формируется с постами одного автора."""
        response = self.author_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.post_2.author}
                    )
        )
        object_page_obj = response.context['page_obj']
        self.assertEqual(
            object_page_obj.object_list[0].author,
            self.post_2.author)
        self.assertEqual(
            object_page_obj.object_list[0].text,
            self.post_2.text)
        self.assertEqual(
            object_page_obj.object_list[0].group,
            self.post_2.group)
        self.assertEqual(len(object_page_obj.object_list), 1)

    def test_post_detail_correct_context(self):
        """Шаблон post_detail формируется с одним постом,
        отфильтрованным по id.
        """
        response = self.author_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post_1.id}
                    )
        )
        object_post_id = response.context['post_id']
        object_post = response.context['post']
        self.assertEqual(object_post_id, self.post_1.id)
        self.assertNotIsInstance(object_post, list)

    def test_paginator_correct_context(self):
        """Шаблоны index, group_posts и profile формируются с
        правильным контекстом для пажинатора.
        """
        Post.objects.bulk_create(
            [Post(author=self.user_1, text='T', group_id=1)] * 15
        )
        for name_page in self.name_page_list:
            with self.subTest(reverse_name=name_page):
                response = self.guest_client.get(name_page)
                posts_in_page = len(response.context['page_obj'].object_list)
                self.assertEqual(posts_in_page, 10)

    def test_post_create_correct_context(self):
        """Шаблон post_create формируется с полями
        формы для создания поста.
        """
        response = self.author_client.get(
            reverse('posts:post_create')
        )
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
        self.assertIsNone(response.context['widget']['value'])
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertIsNone(response.context.get('is_edit', None))

    def test_post_edit_correct_context(self):
        """Шаблон post_edit формируется с полями
        формы для редактирования поста.
        """
        response = self.author_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post_1.id}
                    )
        )
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
        self.assertEqual(
            response.context['widget']['value'], self.post_1.text
        )
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertTrue(response.context['is_edit'])
        self.assertIsInstance(response.context['is_edit'], bool)
