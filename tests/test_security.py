from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from articles.models import Category, Article
from reader_features.models import Comment

User = get_user_model()


class SecurityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="security_tester",
            email="sec@example.com",
            password="StrongPassword123!",
            role=User.Role.READER
        )
        self.category = Category.objects.create(name="Tech", slug="tech")

    def test_open_redirect_defense_on_login(self):
        # Attempt to redirect to external attacker domain
        external_url = "https://malicious-phishing-site.example.com"
        response = self.client.post(f"{reverse('login')}?next={external_url}", {
            'username': 'security_tester',
            'password': 'StrongPassword123!',
        })
        # Must NOT redirect to external URL; must redirect to default safe homepage
        self.assertRedirects(response, reverse('homepage'))

    def test_open_redirect_defense_on_registration(self):
        external_url = "https://evil.com/steal-creds"
        response = self.client.post(f"{reverse('register')}?next={external_url}", {
            'full_name': "Eve Attacker",
            'username': "eve_attacker",
            'email': "eve@example.com",
            'password': "Password999!",
            'confirm_password': "Password999!",
            'accept_terms': True,
        })
        self.assertRedirects(response, reverse('homepage'))

    def test_rich_text_xss_sanitization(self):
        # Attempt XSS injection into Article model content
        malicious_html = """
        <p>Legitimate text</p>
        <script>alert('xss_injection');</script>
        <img src="valid.jpg" onerror="alert('xss_image')">
        <a href="javascript:alert('xss_link')">Click me</a>
        """

        article = Article(
            title="Security Audit of Content Sanitization",
            author=self.user,
            category=self.category,
            excerpt="Excerpt testing security sanitization of HTML rich text.",
            content=malicious_html,
            status=Article.ArticleStatus.DRAFT
        )
        article.save()

        # Verify <script> tag is completely stripped
        self.assertNotIn("<script>", article.content)
        self.assertNotIn("alert('xss_injection')", article.content)

        # Verify onerror attribute is completely removed
        self.assertNotIn("onerror", article.content)

        # Verify javascript: pseudo protocol is removed or invalidated
        self.assertNotIn("javascript:", article.content)

    def test_comment_xss_sanitization(self):
        self.client.login(username="security_tester", password="StrongPassword123!")

        article = Article.objects.create(
            title="Public Story For Comments",
            author=self.user,
            category=self.category,
            excerpt="Testing comments security.",
            content="<p>Story content.</p>",
            status=Article.ArticleStatus.PUBLISHED
        )

        malicious_comment = "<script>alert('hacked')</script>Great article!"
        self.client.post(reverse('add_comment', kwargs={'article_id': article.id}), {
            'content': malicious_comment
        })

        comment = Comment.objects.get(article=article, user=self.user)
        self.assertNotIn("<script>", comment.content)
        self.assertNotIn("alert('hacked')", comment.content)
        self.assertIn("Great article!", comment.content)

    def test_role_escalation_defense_in_registration(self):
        # Attacker tries to inject role and staff flags in POST payload
        response = self.client.post(reverse('register'), {
            'full_name': "Escalation Attacker",
            'username': "escalate_user",
            'email': "escalate@example.com",
            'password': "Password999!",
            'confirm_password': "Password999!",
            'accept_terms': True,
            'role': 'ADMIN',
            'is_staff': True,
            'is_superuser': True,
        })
        self.assertEqual(response.status_code, 302)
        created_user = User.objects.get(username="escalate_user")
        self.assertEqual(created_user.role, User.Role.READER)
        self.assertFalse(created_user.is_staff)
        self.assertFalse(created_user.is_superuser)
