from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from accounts.models import AuthorProfile
from articles.models import Category, Article
from reader_features.models import ReadingHistory
from analytics.models import ArticleView

User = get_user_model()


class AccessRestrictionTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.author = User.objects.create_user(
            username="author_jane",
            email="jane@example.com",
            password="AuthorPassword123!",
            role=User.Role.AUTHOR
        )
        AuthorProfile.objects.create(user=self.author, is_approved=True)

        self.reader = User.objects.create_user(
            username="reader_bob",
            email="bob@example.com",
            password="ReaderPassword123!",
            role=User.Role.READER
        )

        self.category = Category.objects.create(name="Philosophy", slug="philosophy")

        # Secret full body text
        self.secret_body = "CONFIDENTIAL_EDITORIAL_TEXT_THAT_SHOULD_NEVER_LEAK_TO_GUESTS"

        self.published_article = Article.objects.create(
            title="The Ethics of Digital Archiving",
            subtitle="Preserving cultural memory in an ephemeral age",
            slug="ethics-of-digital-archiving",
            author=self.author,
            category=self.category,
            excerpt="Public summary visible to everyone across the web.",
            content=f"<p>{self.secret_body}</p>",
            status=Article.ArticleStatus.PUBLISHED,
            published_at=timezone.now()
        )

        self.draft_article = Article.objects.create(
            title="Unpublished Draft Under Construction",
            slug="unpublished-draft",
            author=self.author,
            category=self.category,
            excerpt="Draft excerpt.",
            content="<p>Draft secret body.</p>",
            status=Article.ArticleStatus.DRAFT
        )

    def test_guest_sees_preview_but_server_protects_full_content(self):
        # Anonymous visitor opens published article
        url = reverse('article_detail', kwargs={'slug': self.published_article.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # 1. Headline, author, category, excerpt are visible
        self.assertContains(response, self.published_article.title)
        self.assertContains(response, self.published_article.excerpt)
        self.assertContains(response, self.author.username)
        self.assertContains(response, self.category.name)

        # 2. Server-side check: full article body MUST NOT be present in response HTML!
        self.assertNotContains(response, self.secret_body)

        # 3. Access restriction block is present
        self.assertContains(response, "Enjoying this story?")
        self.assertContains(response, "Log In to Continue")
        self.assertContains(response, "Create Free Account")
        self.assertContains(response, f"next={url}")

    def test_authenticated_reader_sees_full_content(self):
        # Reader logs in
        self.client.login(username="reader_bob", password="ReaderPassword123!")
        url = reverse('article_detail', kwargs={'slug': self.published_article.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Full content IS delivered to authenticated reader
        self.assertContains(response, self.secret_body)

        # Access restriction block is NOT rendered
        self.assertNotContains(response, "Enjoying this story?")
        self.assertNotContains(response, "Log In to Continue")

        # Reading history is logged
        self.assertTrue(ReadingHistory.objects.filter(user=self.reader, article=self.published_article).exists())

        # View telemetry is recorded
        self.assertTrue(ArticleView.objects.filter(article=self.published_article, user=self.reader).exists())

    def test_unpublished_draft_inaccessible_to_guest_and_ordinary_reader(self):
        url = reverse('article_detail', kwargs={'slug': self.draft_article.slug})

        # Anonymous visitor -> 404
        guest_res = self.client.get(url)
        self.assertEqual(guest_res.status_code, 404)

        # Authenticated non-owner reader -> 404
        self.client.login(username="reader_bob", password="ReaderPassword123!")
        reader_res = self.client.get(url)
        self.assertEqual(reader_res.status_code, 404)

        # Author owner -> 200 (preview mode)
        self.client.login(username="author_jane", password="AuthorPassword123!")
        author_res = self.client.get(url)
        self.assertEqual(author_res.status_code, 200)
        self.assertContains(author_res, "Draft Editorial Preview Mode")
