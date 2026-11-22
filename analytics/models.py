from django.conf import settings
from django.db import models


class ArticleView(models.Model):
    article = models.ForeignKey('articles.Article', on_delete=models.CASCADE, related_name='views_log')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    session_key = models.CharField(max_length=64, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"View for '{self.article.title}' at {self.timestamp}"
