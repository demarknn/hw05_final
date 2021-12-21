from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache

from posts.models import Follow, Group, Post

User = get_user_model()


class ViewsTests(TestCase):
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
            text='Тестовый текст поста',
            author=ViewsTests.user,
            group=ViewsTests.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_posts',
                    kwargs={'slug': self.group.slug}): ('posts/group_list.html'
                                                        ),
            reverse('posts:profile',
                    kwargs={'username': self.user}): ('posts/profile.html'),
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}): (
                'posts/post_detail.html'
            ),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}): (
                'posts/create_post.html'
            ),
            reverse('posts:post_create'): 'posts/create_post.html'
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        post_test = response.context['page_obj'][0]
        self.assertEqual(post_test.text, self.post.text)
        self.assertEqual(post_test.author, self.post.author)
        self.assertEqual(post_test.group, self.post.group)
        self.assertEqual(post_test.image, self.post.image)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse(
            'posts:group_posts', kwargs={'slug': self.group.slug}))
        post_test = response.context['posts'][0]
        self.assertEqual(post_test.image, self.post.image)
        self.assertEqual(post_test, self.post)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse(
            'posts:profile', kwargs={'username': self.user}))
        post_test = response.context['page_obj'][0]
        self.assertEqual(post_test, self.post)
        self.assertEqual(post_test.image, self.post.image)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        post_test = response.context['post']
        self.assertEqual(post_test, self.post)
        self.assertEqual(post_test.image, self.post.image)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id})
        )
        form_field_text = response.context['form'].initial['text']
        form_field_group = response.context['form'].initial['group']
        self.assertEqual(form_field_text, self.post.text)
        self.assertEqual(form_field_group, self.post.group.id)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_create'))
        form_field_text = response.context['form'].initial
        self.assertEqual(form_field_text, {})

    def test_create_post_in_index_group_profile(self):
        templates_pages_names = {
            reverse('posts:index'): 'index',
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}): 'group_posts',
            reverse(
                'posts:profile', kwargs={'username': self.user}): 'profile',
        }
        for reverse_name in templates_pages_names.keys():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                post_test = response.context['page_obj'][0]
                self.assertEqual(post_test, self.post)

    def test_create_post_not_another_group(self):
        anothergroup = Group.objects.create(
            title='anothergroup',
            description='anothergroup описание',
            slug='anothergroup'
        )
        response = self.authorized_client.get(reverse(
            'posts:group_posts', kwargs={'slug': anothergroup.slug}))
        post_test = response.context['page_obj']
        self.assertNotEqual(post_test, self.post)

    def test_index_cache(self):
        post = Post.objects.create(
            text='Тестовый текст поста кэша',
            author=ViewsTests.user
        )
        response = self.authorized_client.get(reverse('posts:index'))
        post_create = response.content
        post.delete()
        response = self.authorized_client.get(reverse('posts:index'))
        post_delete = response.content
        self.assertEqual(post_create, post_delete)
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        cache_delete = response.content
        self.assertNotEqual(cache_delete, post_delete)

    def test_follow_new_post(self):
        follower = User.objects.create(username='follower')
        not_follower = User.objects.create(username='not_follower')
        authorized_client = Client()
        authorized_client.force_login(follower)
        Follow.objects.create(user=follower, author=self.user)
        response = authorized_client.get(reverse('posts:follow_index'))
        post_test = response.context['page_obj'][0]
        self.assertEqual(post_test, self.post)
        authorized_client.force_login(not_follower)
        response_not_follower = authorized_client.get(
            reverse('posts:follow_index')
        )
        post_test_not_follower = response_not_follower.context['page_obj']
        self.assertNotEqual(post_test, post_test_not_follower)

    def test_follow_authorized_client(self):
        follower = User.objects.create(username='follower')
        Follow.objects.create(user=follower, author=self.user)
        following = (
            Follow.objects.filter(
                user=follower).filter(author=self.user).exists()
        )
        self.assertTrue(following)
        Follow.objects.filter(user=follower, author=self.user).delete()
        following = (
            Follow.objects.filter(
                user=follower).filter(author=self.user).exists()
        )
        self.assertFalse(following)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            description='Тестовое описание',
            slug='slug_test'
        )
        cls.user = User.objects.create(username='HasNoName')
        objs = [
            Post(
                text='Тестовый текст поста' + str(i),
                id=i,
                author=PaginatorViewsTest.user,
                group=PaginatorViewsTest.group
            )
            for i in range(15)
        ]
        cls.post = Post.objects.bulk_create(objs, batch_size=15)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_first_contains_ten_records(self):
        first_page = 10
        templates_pages_names = {
            reverse('posts:index'): '',
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}): '',
            reverse('posts:profile', kwargs={'username': self.user}): '',
        }
        for reverse_name in templates_pages_names.keys():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), first_page)

    def test_second_page_contains_three_records(self):
        second_page = 5
        templates_pages_names = {
            reverse('posts:index'): '',
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}): '',
            reverse('posts:profile', kwargs={'username': self.user}): '',
        }
        for reverse_name in templates_pages_names.keys():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']), second_page)
