import math
import re
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
import bleach


ALLOWED_TAGS = [
    'p', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'em', 'b', 'i', 'u', 'strike',
    'blockquote', 'ul', 'ol', 'li', 'a', 'img', 'pre', 'code', 'table', 'thead',
    'tbody', 'tr', 'th', 'td', 'br', 'hr', 'figure', 'figcaption', 'span', 'div'
]
ALLOWED_ATTRIBUTES = {
    '*': ['class'],
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
}


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='bi-newspaper', help_text='Bootstrap Icon class')
    accent_color = models.CharField(max_length=30, default='#800020', help_text='Hex color code')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"#{self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Article(models.Model):
    class ArticleType(models.TextChoices):
        NEWS = 'NEWS', 'News'
        OPINION = 'OPINION', 'Opinion'
        FEATURE = 'FEATURE', 'Feature Story'
        EDITORIAL = 'EDITORIAL', 'Editorial'
        INTERVIEW = 'INTERVIEW', 'Interview'
        LONGFORM = 'LONGFORM', 'Long-form Investigation'

    class ArticleStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SUBMITTED = 'SUBMITTED', 'Submitted for Review'
        CHANGES_REQUESTED = 'CHANGES_REQUESTED', 'Changes Requested'
        APPROVED = 'APPROVED', 'Approved'
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        PUBLISHED = 'PUBLISHED', 'Published'
        REJECTED = 'REJECTED', 'Rejected'
        ARCHIVED = 'ARCHIVED', 'Archived'

    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=350, blank=True)
    slug = models.SlugField(max_length=280, unique=True, db_index=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='articles')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='articles')
    tags = models.ManyToManyField(Tag, blank=True, related_name='articles')
    article_type = models.CharField(max_length=20, choices=ArticleType.choices, default=ArticleType.NEWS)
    
    # Public preview excerpt (safe to show unauthenticated readers)
    excerpt = models.TextField(max_length=600, help_text='Short teaser shown to public visitors.')
    
    # Protected content: full rich text, sanitised, server-side guarded
    content = models.TextField(help_text='Full article content. Protected server-side.')
    
    cover_image = models.ImageField(upload_to='article_covers/', blank=True, null=True)
    cover_caption = models.CharField(max_length=255, blank=True)
    cover_credit = models.CharField(max_length=150, blank=True)

    status = models.CharField(max_length=20, choices=ArticleStatus.choices, default=ArticleStatus.DRAFT, db_index=True)
    
    word_count = models.PositiveIntegerField(default=0)
    estimated_reading_time = models.PositiveIntegerField(default=1, help_text='Estimated reading time in minutes')
    views_count = models.PositiveIntegerField(default=0)
    
    is_featured = models.BooleanField(default=False, help_text='Show in top featured hero banner')
    is_editors_pick = models.BooleanField(default=False, help_text='Show in Editor\'s Picks carousel')
    is_trending = models.BooleanField(default=False, help_text='Manually flag or algorithmically elevated')

    sources = models.TextField(blank=True, help_text='Optional primary sources or citations')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title

    @property
    def is_publicly_readable(self):
        return self.status == self.ArticleStatus.PUBLISHED and (
            self.published_at is None or self.published_at <= timezone.now()
        )

    def calculate_metrics(self):
        # Strip html tags to calculate word count
        clean_text = re.sub(r'<[^>]+>', ' ', self.content or '')
        words = len(clean_text.split())
        self.word_count = words
        # 200 words per minute average reading speed
        self.estimated_reading_time = max(1, math.ceil(words / 200)) if words > 0 else 1

    def sanitize_content(self):
        if self.content:
            # Strip script and style tags completely including their inner text
            clean_html = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', self.content, flags=re.DOTALL | re.IGNORECASE)
            self.content = bleach.clean(
                clean_html,
                tags=ALLOWED_TAGS,
                attributes=ALLOWED_ATTRIBUTES,
                strip=True
            )

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or 'article'
            unique_slug = base_slug
            counter = 1
            while Article.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug

        self.sanitize_content()
        self.calculate_metrics()

        # If transitioning to PUBLISHED without a published_at date, set to now
        if self.status == self.ArticleStatus.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)


class ArticleImage(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='article_gallery/', blank=True, null=True)
    image_url = models.URLField(blank=True, help_text="Direct link or CDN URL for high-res photo")
    caption = models.CharField(max_length=255, blank=True)
    credit = models.CharField(max_length=150, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Image for '{self.article.title}': {self.caption[:30]}"

    @property
    def url(self):
        if self.image:
            return self.image.url
        return self.image_url or ''


class ArticleReview(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='reviewed_articles')
    action = models.CharField(max_length=30)
    feedback = models.TextField(help_text='Feedback notes or revision requirements.')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action} on '{self.article.title}' by {self.reviewer}"
