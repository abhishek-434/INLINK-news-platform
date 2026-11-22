from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import AuthorProfile
from articles.models import Category, Article, ArticleReview

User = get_user_model()


class PublishingWorkflowTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.author = User.objects.create_user(
            username="test_author",
            email="author@example.com",
            password="AuthorPassword123!",
            role=User.Role.AUTHOR
        )
        AuthorProfile.objects.create(user=self.author, is_approved=True)

        self.admin = User.objects.create_user(
            username="test_admin",
            email="admin@example.com",
            password="AdminPassword123!",
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True
        )

        self.category = Category.objects.create(name="Science", slug="science")

    def test_author_create_draft_and_submit_review(self):
        self.client.login(username="test_author", password="AuthorPassword123!")

        # 1. Author saves draft
        res = self.client.post(reverse('author_article_create'), {
            'title': "Valid Headline for Scientific Breakthrough",
            'subtitle': "A secondary explanation deck",
            'category': self.category.id,
            'article_type': Article.ArticleType.NEWS,
            'excerpt': "This is an excerpt of sufficient length exceeding thirty characters for test validation.",
            'content': "<p>This is a formatted body containing over one hundred characters to satisfy validation constraints of the article form.</p>",
            'action': 'save_draft'
        })
        self.assertEqual(res.status_code, 302)
        article = Article.objects.get(slug="valid-headline-for-scientific-breakthrough")
        self.assertEqual(article.status, Article.ArticleStatus.DRAFT)

        # 2. Author submits for review
        res_submit = self.client.post(reverse('author_article_edit', kwargs={'pk': article.pk}), {
            'title': "Valid Headline for Scientific Breakthrough",
            'subtitle': "A secondary explanation deck",
            'category': self.category.id,
            'article_type': Article.ArticleType.NEWS,
            'excerpt': "This is an excerpt of sufficient length exceeding thirty characters for test validation.",
            'content': "<p>This is a formatted body containing over one hundred characters to satisfy validation constraints of the article form.</p>",
            'action': 'submit_review'
        })
        self.assertEqual(res_submit.status_code, 302)
        article.refresh_from_db()
        self.assertEqual(article.status, Article.ArticleStatus.SUBMITTED)

    def test_admin_approve_and_publish_article(self):
        # Create submitted article
        article = Article.objects.create(
            title="A Story Ready for Approval",
            author=self.author,
            category=self.category,
            excerpt="Summary of the article awaiting editorial review by administration.",
            content="<p>Full content of the article ready for approval by the editorial board.</p>",
            status=Article.ArticleStatus.SUBMITTED
        )

        # Admin logs in
        self.client.login(username="test_admin", password="AdminPassword123!")
        res = self.client.post(reverse('admin_review_detail', kwargs={'pk': article.pk}), {
            'action': 'approve_publish',
            'feedback': 'Excellent piece, approved for publishing.'
        })
        self.assertEqual(res.status_code, 302)
        article.refresh_from_db()
        self.assertEqual(article.status, Article.ArticleStatus.PUBLISHED)
        self.assertIsNotNone(article.published_at)

    def test_admin_request_changes_and_reject(self):
        article = Article.objects.create(
            title="A Story Needing Changes",
            author=self.author,
            category=self.category,
            excerpt="Summary of the article needing revision before going live.",
            content="<p>Content requiring verification of citations and tone adjustments.</p>",
            status=Article.ArticleStatus.SUBMITTED
        )

        self.client.login(username="test_admin", password="AdminPassword123!")
        
        # Request changes
        self.client.post(reverse('admin_review_detail', kwargs={'pk': article.pk}), {
            'action': 'request_changes',
            'feedback': 'Please check primary source on paragraph 2.'
        })
        article.refresh_from_db()
        self.assertEqual(article.status, Article.ArticleStatus.CHANGES_REQUESTED)
        self.assertTrue(ArticleReview.objects.filter(article=article, action="CHANGES REQUESTED").exists())

        # Reject
        self.client.post(reverse('admin_review_detail', kwargs={'pk': article.pk}), {
            'action': 'reject',
            'feedback': 'Does not meet editorial guidelines.'
        })
        article.refresh_from_db()
        self.assertEqual(article.status, Article.ArticleStatus.REJECTED)
