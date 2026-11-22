from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testreader",
            email="testreader@example.com",
            password="StrongPassword123!",
            role=User.Role.READER
        )

    def test_reader_registration_success(self):
        response = self.client.post(reverse('register'), {
            'full_name': "Alice Walker",
            'username': "alicew",
            'email': "alice@example.com",
            'password': "Password999!",
            'confirm_password': "Password999!",
            'accept_terms': True,
        })
        self.assertEqual(response.status_code, 302)
        new_user = User.objects.get(username="alicew")
        self.assertEqual(new_user.role, User.Role.READER)
        self.assertFalse(new_user.is_staff)
        self.assertFalse(new_user.is_superuser)

    def test_registration_prevents_duplicate_email(self):
        response = self.client.post(reverse('register'), {
            'full_name': "Duplicate Test",
            'username': "newuser",
            'email': "testreader@example.com",
            'password': "Password999!",
            'confirm_password': "Password999!",
            'accept_terms': True,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email', "An account with this email address already exists.")

    def test_login_success_and_logout(self):
        login_res = self.client.post(reverse('login'), {
            'username': 'testreader',
            'password': 'StrongPassword123!',
        })
        self.assertEqual(login_res.status_code, 302)

        logout_res = self.client.get(reverse('logout'))
        self.assertEqual(logout_res.status_code, 302)

    def test_login_invalid_credentials(self):
        response = self.client.post(reverse('login'), {
            'username': 'testreader',
            'password': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password")

    def test_safe_post_login_redirect(self):
        # Create published article for safe redirect target
        from articles.models import Category, Article
        from django.utils import timezone
        cat = Category.objects.create(name="Tech", slug="tech")
        art = Article.objects.create(
            title="Redirect Target Article",
            slug="test-article-slug",
            author=self.user,
            category=cat,
            excerpt="Excerpt for redirect test.",
            content="<p>Full content for redirect test.</p>",
            status=Article.ArticleStatus.PUBLISHED,
            published_at=timezone.now()
        )
        target_path = f"/articles/{art.slug}/"
        response = self.client.post(f"{reverse('login')}?next={target_path}", {
            'username': 'testreader',
            'password': 'StrongPassword123!',
        })
        self.assertRedirects(response, target_path)
