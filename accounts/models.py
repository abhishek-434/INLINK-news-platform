from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        READER = 'READER', 'Reader'
        AUTHOR = 'AUTHOR', 'Author'
        ADMIN = 'ADMIN', 'Administrator'

    email = models.EmailField(unique=True, verbose_name='Email Address')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.READER)
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    @property
    def is_reader(self):
        return self.role == self.Role.READER

    @property
    def is_author(self):
        return self.role == self.Role.AUTHOR or hasattr(self, 'author_profile') and self.author_profile.is_approved

    @property
    def is_administrator(self):
        return self.role == self.Role.ADMIN or self.is_superuser or self.is_staff

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class AuthorProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='author_profile')
    pen_name = models.CharField(max_length=100, blank=True)
    tagline = models.CharField(max_length=200, blank=True, help_text="e.g. Senior Investigative Tech Reporter")
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='author_profiles/', blank=True, null=True)
    writing_interests = models.CharField(max_length=300, blank=True, help_text="e.g. Artificial Intelligence, Climate Science, Geopolitics")
    website_url = models.URLField(blank=True, null=True)
    twitter_handle = models.CharField(max_length=50, blank=True)
    linkedin_url = models.URLField(blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    is_suspended = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def display_name(self):
        if self.pen_name:
            return self.pen_name
        full = f"{self.user.first_name} {self.user.last_name}".strip()
        return full if full else self.user.username

    def __str__(self):
        return f"Author Profile: {self.display_name()} ({self.user.username})"


class AuthorApplication(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='author_applications')
    full_name = models.CharField(max_length=150)
    bio = models.TextField(help_text="Brief professional background and editorial focus.")
    writing_interests = models.CharField(max_length=300, help_text="Primary beats (e.g. Tech, Culture, Global Economy).")
    experience_years = models.PositiveIntegerField(default=1, help_text="Years of professional or amateur writing experience.")
    portfolio_url = models.URLField(blank=True, null=True, help_text="Link to published works, portfolio or personal blog.")
    sample_writing = models.TextField(blank=True, help_text="A writing sample or pitch.")
    profile_picture = models.ImageField(upload_to='application_photos/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    admin_notes = models.TextField(blank=True, help_text="Internal notes or reason for rejection/approval.")
    reviewed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_author_applications'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Application by {self.full_name} ({self.user.username}) - {self.get_status_display()}"
