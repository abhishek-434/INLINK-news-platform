from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from accounts.models import AuthorProfile
from articles.models import Category, Article
from reader_features.models import Bookmark, Comment, AuthorFollow

User = get_user_model()


class ReaderFeatureTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.author = User.objects.create_user(
            username="author_victor",
            email="victor@example.com",
            password="AuthorPassword123!",
            role=User.Role.AUTHOR
        )
        AuthorProfile.objects.create(user=self.author, is_approved=True)

        self.reader = User.objects.create_user(
            username="reader_grace",
            email="grace@example.com",
            password="ReaderPassword123!",
            role=User.Role.READER
        )

        self.category = Category.objects.create(name="Design", slug="design")

        self.article = Article.objects.create(
            title="Design Principles of Dieter Rams",
            slug="design-principles-dieter-rams",
            author=self.author,
            category=self.category,
            excerpt="Less, but better. Examining functional minimalism in industrial craft.",
            content="<p>Full article body on functionalist craft and typography.</p>",
            status=Article.ArticleStatus.PUBLISHED,
            published_at=timezone.now()
        )

    def test_bookmark_and_unbookmark(self):
        self.client.login(username="reader_grace", password="ReaderPassword123!")

        # 1. Add bookmark
        res = self.client.post(reverse('toggle_bookmark', kwargs={'article_id': self.article.id}))
        self.assertEqual(res.status_code, 302)
        self.assertTrue(Bookmark.objects.filter(user=self.reader, article=self.article).exists())

        # 2. Toggle again to remove
        res2 = self.client.post(reverse('toggle_bookmark', kwargs={'article_id': self.article.id}))
        self.assertEqual(res2.status_code, 302)
        self.assertFalse(Bookmark.objects.filter(user=self.reader, article=self.article).exists())

    def test_submit_and_delete_comment(self):
        self.client.login(username="reader_grace", password="ReaderPassword123!")

        # Post comment
        res = self.client.post(reverse('add_comment', kwargs={'article_id': self.article.id}), {
            'content': 'Remarkable insights on functional ergonomics.'
        })
        self.assertEqual(res.status_code, 302)
        comment = Comment.objects.get(article=self.article, user=self.reader)
        self.assertEqual(comment.content, 'Remarkable insights on functional ergonomics.')

        # Delete own comment
        del_res = self.client.post(reverse('delete_comment', kwargs={'comment_id': comment.id}))
        self.assertEqual(del_res.status_code, 302)
        self.assertFalse(Comment.objects.filter(id=comment.id).exists())

    def test_follow_and_unfollow_author(self):
        self.client.login(username="reader_grace", password="ReaderPassword123!")

        # Follow
        res = self.client.post(reverse('toggle_follow_author', kwargs={'author_id': self.author.id}))
        self.assertEqual(res.status_code, 302)
        self.assertTrue(AuthorFollow.objects.filter(follower=self.reader, author=self.author).exists())

        # Unfollow
        res2 = self.client.post(reverse('toggle_follow_author', kwargs={'author_id': self.author.id}))
        self.assertEqual(res2.status_code, 302)
        self.assertFalse(AuthorFollow.objects.filter(follower=self.reader, author=self.author).exists())
