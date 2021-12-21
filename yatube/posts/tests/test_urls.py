from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.core.cache import cache

from posts.models import Group, Post

User = get_user_model()


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовый текст',
            slug='slug_test'
        )
        cls.user_author = User.objects.create(username='HasNoName')
        cls.user_login = User.objects.create(username='NoName_login')
        cls.post = Post.objects.create(
            text='Тестовый заголовок',
            author=URLTests.user_author,
            group=URLTests.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_author)
        self.url_index = '/'
        self.url_group_slug = f'/group/{self.group.slug}/'
        self.url_profile = f'/profile/{self.user_author}/'
        self.url_post_id = f'/posts/{self.post.id}/'
        self.url_post_edit = f'/posts/{self.post.id}/edit/'
        self.url_post_create = '/create/'
        cache.clear()

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            self.url_index: 'posts/index.html',
            self.url_group_slug: 'posts/group_list.html',
            self.url_profile: 'posts/profile.html',
            self.url_post_id: 'posts/post_detail.html',
            self.url_post_edit: 'posts/create_post.html',
            self.url_post_create: 'posts/create_post.html'
        }
        for adress, template in templates_url_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_author_client(self):
        """URL-адрес доступен для автора."""
        templates_url_names = {
            self.url_index: HTTPStatus.OK,
            self.url_group_slug: HTTPStatus.OK,
            self.url_profile: HTTPStatus.OK,
            self.url_post_id: HTTPStatus.OK,
            self.url_post_edit: HTTPStatus.OK,
            self.url_post_create: HTTPStatus.OK
        }
        for adress, status in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, status)

    def test_urls_uses_guest_client(self):
        """URL-адрес доступен для любого пользователя."""
        templates_url_names = {
            self.url_index: HTTPStatus.OK,
            self.url_group_slug: HTTPStatus.OK,
            self.url_profile: HTTPStatus.OK,
            self.url_post_id: HTTPStatus.OK,
            self.url_post_edit: HTTPStatus.FOUND,
            self.url_post_create: HTTPStatus.FOUND
        }
        for adress, status in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, status)

    def test_urls_uses_authorized_client(self):
        """URL-адрес доступен для авторизованного пользователя."""
        self.authorized_client.force_login(self.user_login)
        templates_url_names = {
            self.url_index: HTTPStatus.OK,
            self.url_group_slug: HTTPStatus.OK,
            self.url_profile: HTTPStatus.OK,
            self.url_post_id: HTTPStatus.OK,
            self.url_post_edit: HTTPStatus.FOUND,
            self.url_post_create: HTTPStatus.OK
        }
        for adress, status in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, status)

    def test_url_404(self):
        response = self.guest_client.get('/ne_sushchestvuyushchaya_stranica')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_index_uses_correct_template(self):
        """Страница / использует шаблон posts/index.html."""
        response = self.authorized_client.get(self.url_index)
        self.assertTemplateUsed(response, 'posts/index.html')

    def test_profile_username_uses_correct_template(self):
        """Страница profile/<username> использует шаблон posts/profile.html."""
        response = self.authorized_client.get(self.url_profile)
        self.assertTemplateUsed(response, 'posts/profile.html')

    def test_group_slug_uses_correct_template(self):
        """Страница /group/<slug> использует шаблон posts/group_list.html."""
        response = self.authorized_client.get(self.url_group_slug)
        self.assertTemplateUsed(response, 'posts/group_list.html')

    def test_post_id_uses_correct_template(self):
        """Страница post_id использует шаблон posts/post_detail.html."""
        response = self.authorized_client.get(self.url_post_id)
        self.assertTemplateUsed(response, 'posts/post_detail.html')

    def test_post_id_edit_uses_correct_template(self):
        """Страница posts_edit использует шаблон posts/create_post.html."""
        response = self.authorized_client.get(self.url_post_edit)
        self.assertTemplateUsed(response, 'posts/create_post.html')


class StaticURLTests(TestCase):
    def setUp(self) -> None:
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about(self):
        response = self.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_tech(self):
        response = self.guest_client.get('/about/tech/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
