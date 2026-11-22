from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import AuthorProfile
from articles.models import Category, Article

User = get_user_model()


class PermissionTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Reader user
        self.reader = User.objects.create_user(
            username="plain_reader",
            email="reader@example.com",
            password="Password123!",
            role=User.Role.READER
        )

        # Author user 1
        self.author1 = User.objects.create_user(
            username="author_one",
            email="author1@example.com",
            password="Password123!",
            role=User.Role.AUTHOR
        )
        AuthorProfile.objects.create(user=self.author1, is_approved=True)

        # Author user 2
        self.author2 = User.objects.create_user(
            username="author_two",
            email="author2@example.com",
            password="Password123!",
            role=User.Role.AUTHOR
        )
        AuthorProfile.objects.create(user=self.author2, is_approved=True)

        # Admin user
        self.admin = User.objects.create_user(
            username="editor_admin",
            email="admin@example.com",
            password="Password123!",
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True
        )

        self.category = Category.objects.create(name="Tech", slug="tech")

        # Author 1's draft
        self.draft = Article.objects.create(
            title="Secret Draft of Author 1",
            author=self.author1,
            category=self.category,
            excerpt="Excerpt of draft.",
            content="<p>Full confidential draft content.</p>",
            status=Article.ArticleStatus.DRAFT
        )

    def test_reader_cannot_access_author_dashboard(self):
        self.client.login(username="plain_reader", password="Password123!")
        res = self.client.get(reverse('author_overview'))
        self.assertEqual(res.status_code, 302)
        self.assertIn('/author-application/', res.url)

    def test_reader_cannot_access_admin_dashboard(self):
        self.client.login(username="plain_reader", password="Password123!")
        res = self.client.get(reverse('admin_overview'))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, '/')

    def test_author_cannot_access_admin_dashboard(self):
        self.client.login(username="author_one", password="Password123!")
        res = self.client.get(reverse('admin_overview'))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, '/')

    def test_author_cannot_edit_another_authors_draft(self):
        # Author 2 tries to edit Author 1's draft
        self.client.login(username="author_two", password="Password123!")
        res = self.client.get(reverse('author_article_edit', kwargs={'pk': self.draft.pk}))
        self.assertEqual(res.status_code, 404)

    def test_author_cannot_delete_another_authors_draft(self):
        self.client.login(username="author_two", password="Password123!")
        res = self.client.post(reverse('author_article_delete', kwargs={'pk': self.draft.pk}))
        self.assertEqual(res.status_code, 404)
        self.assertTrue(Article.objects.filter(pk=self.draft.pk).exists())
