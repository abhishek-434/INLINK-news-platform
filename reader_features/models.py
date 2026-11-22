from django.conf import settings
from django.db import models


class Bookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookmarks')
    article = models.ForeignKey('articles.Article', on_delete=models.CASCADE, related_name='bookmarked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'article')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} saved '{self.article.title}'"


class ReadingHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reading_history')
    article = models.ForeignKey('articles.Article', on_delete=models.CASCADE, related_name='reader_histories')
    last_read_at = models.DateTimeField(auto_now=True)
    progress_percent = models.PositiveIntegerField(default=100)

    class Meta:
        unique_together = ('user', 'article')
        ordering = ['-last_read_at']

    def __str__(self):
        return f"{self.user.username} read '{self.article.title}'"


class AuthorFollow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='following_authors')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='author_followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'author')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.follower.username} follows {self.author.username}"


class Comment(models.Model):
    article = models.ForeignKey('articles.Article', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='article_comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content = models.TextField()
    is_approved = models.BooleanField(default=True)
    is_flagged = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on '{self.article.title}'"


class ArticleReport(models.Model):
    class Reason(models.TextChoices):
        INACCURATE = 'INACCURATE', 'Factual Inaccuracy'
        PLAGIARISM = 'PLAGIARISM', 'Plagiarism / Copyright'
        OFFENSIVE = 'OFFENSIVE', 'Offensive / Hate Speech'
        SPAM = 'SPAM', 'Spam / Commercial'
        OTHER = 'OTHER', 'Other Policy Violation'

    article = models.ForeignKey('articles.Article', on_delete=models.CASCADE, related_name='reports')
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submitted_reports')
    reason = models.CharField(max_length=30, choices=Reason.choices, default=Reason.OTHER)
    details = models.TextField(help_text='Explain why this article violates editorial standards.')
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_article_reports'
    )
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report on '{self.article.title}' by {self.reported_by.username} ({self.get_reason_display()})"


class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification to {self.recipient.username}: {self.title}"
