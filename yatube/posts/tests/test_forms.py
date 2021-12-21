from http import HTTPStatus
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Group, Post
from posts.models import Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            description='Тестовое описание',
            slug='slug_test'
        )
        cls.user = User.objects.create(username='HasNoName')
        cls.post = Post.objects.create(
            text='Старый текст поста',
            author=PostFormTests.user,
            group=PostFormTests.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'текстформа',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        created_post = Post.objects.get(text=form_data['text'])
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
            ).exists()
        )
        self.assertEqual(form_data['text'], created_post.text)
        self.assertEqual(self.post.author, created_post.author)
        self.assertEqual(self.post.group, created_post.group)

    def test_edit_post(self):
        """Форма редактирует запись в Post."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'новаятекстформа',
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        redirect = reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}
        )
        post = Post.objects.get(id=self.post.id)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), post_count)
        self.assertRedirects(response, redirect)
        self.assertEqual(post.text, form_data['text'])

    def test_create_post_guest_client(self):
        """Гость не может создать запись в Post."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'текстформа',
            'group': self.group.id
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        redirect = (reverse('users:login') + '?next=' + reverse(
            'posts:post_create'
        ))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, redirect)
        self.assertEqual(Post.objects.count(), post_count)
        self.assertFalse(
            Post.objects.filter(
                text=form_data['text'],
            ).exists()
        )

    def test_edit_post_guest_client(self):
        """Гость не может редактировать запись в Post."""
        form_data = {
            'text': 'новаятекстформа',
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        redirect = (reverse('users:login') + '?next=' + reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}
        ))
        post = Post.objects.get(id=self.post.id)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, redirect)
        self.assertNotEqual(post.text, form_data['text'])

    def test_create_comment(self):
        """Авторизованный пользователь может комментировать."""
        comm_count = Comment.objects.count()
        form_data = {
            'text': 'текстформа',
            'post_id': self.post.id
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), comm_count + 1)
        created_comm = Comment.objects.get(text=form_data['text'])
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text'],
            ).exists()
        )
        self.assertEqual(form_data['text'], created_comm.text)
        self.assertEqual(self.post.author, created_comm.author)

    def test_guest_create_comment(self):
        """Гость не может комментировать."""
        comm_count = Comment.objects.count()
        form_data = {
            'text': 'текстформа',
            'post_id': self.post.id
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        redirect = (reverse('users:login') + '?next=' + reverse(
            'posts:add_comment', kwargs={'post_id': self.post.id}
        ))
        self.assertRedirects(response, redirect)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), comm_count)
        self.assertFalse(
            Comment.objects.filter(
                text=form_data['text'],
            ).exists()
        )

    def test_create_image_task(self):
        """Форма создает запись c картинкой в Post."""
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'текстформа',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        created_post = Post.objects.get(text=form_data['text'])
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                image='posts/small.gif'
            ).exists()
        )
        self.assertEqual(form_data['text'], created_post.text)
        self.assertEqual(form_data['image'], uploaded)
        self.assertEqual(self.post.author, created_post.author)
        self.assertEqual(self.post.group, created_post.group)
