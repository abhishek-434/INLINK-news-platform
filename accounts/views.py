from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import CustomUser, AuthorProfile, AuthorApplication
from .forms import (
    ReaderRegistrationForm,
    ReaderLoginForm,
    AuthorApplicationForm,
    UserProfileUpdateForm,
    AuthorProfileUpdateForm,
)
from .permissions import get_safe_redirect


def register_view(request):
    if request.user.is_authenticated:
        return redirect('homepage')

    next_url = request.GET.get('next', '')

    if request.method == 'POST':
        form = ReaderRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in directly after registration
            login(request, user)
            messages.success(
                request,
                f"Welcome to INKLINE, {user.first_name or user.username}! Your free reading membership is now active."
            )
            destination = get_safe_redirect(request, default='homepage')
            return redirect(destination)
        else:
            messages.error(request, "Please correct the errors in the registration form below.")
    else:
        form = ReaderRegistrationForm()

    return render(request, 'authentication/register.html', {
        'form': form,
        'next': next_url,
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect('homepage')

    next_url = request.GET.get('next', '')

    if request.method == 'POST':
        form = ReaderLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}.")
            destination = get_safe_redirect(request, default='homepage')
            return redirect(destination)
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = ReaderLoginForm()

    return render(request, 'authentication/login.html', {
        'form': form,
        'next': next_url,
    })


def logout_view(request):
    logout(request)
    messages.info(request, "You have been successfully signed out.")
    return redirect('homepage')


@login_required
def author_application_view(request):
    # Check if already approved author
    if hasattr(request.user, 'author_profile') and request.user.author_profile.is_approved:
        messages.info(request, "You are already an approved author on INKLINE.")
        return redirect('author_overview')

    # Check for existing pending application
    existing_app = AuthorApplication.objects.filter(user=request.user).first()
    if existing_app and existing_app.status == AuthorApplication.Status.PENDING:
        return redirect('author_application_status')

    if request.method == 'POST':
        form = AuthorApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            app = form.save(commit=False)
            app.user = request.user
            app.status = AuthorApplication.Status.PENDING
            app.save()
            messages.success(
                request,
                "Your author application has been submitted to our editorial board. We will review your pitch promptly."
            )
            return redirect('author_application_status')
    else:
        initial = {
            'full_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
        }
        form = AuthorApplicationForm(initial=initial)

    return render(request, 'authentication/author_application.html', {
        'form': form,
        'existing_app': existing_app,
    })


@login_required
def author_application_status_view(request):
    applications = AuthorApplication.objects.filter(user=request.user).order_by('-created_at')
    latest_app = applications.first()

    return render(request, 'authentication/author_status.html', {
        'latest_app': latest_app,
        'applications': applications,
    })


@login_required
def profile_settings_view(request):
    user = request.user
    user_form = UserProfileUpdateForm(instance=user)
    author_form = None

    if hasattr(user, 'author_profile'):
        author_form = AuthorProfileUpdateForm(instance=user.author_profile)

    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        if form_type == 'user_profile':
            user_form = UserProfileUpdateForm(request.POST, instance=user)
            if user_form.is_valid():
                user_form.save()
                messages.success(request, "Your profile details have been updated.")
                return redirect('profile_settings')
        elif form_type == 'author_profile' and hasattr(user, 'author_profile'):
            author_form = AuthorProfileUpdateForm(request.POST, request.FILES, instance=user.author_profile)
            if author_form.is_valid():
                author_form.save()
                messages.success(request, "Your author bio and public information have been updated.")
                return redirect('profile_settings')

    return render(request, 'authentication/profile_settings.html', {
        'user_form': user_form,
        'author_form': author_form,
    })


def verify_email_view(request, token):
    try:
        user = CustomUser.objects.get(email_verification_token=token)
        user.is_email_verified = True
        user.email_verification_token = None
        user.save()
        messages.success(request, "Your email address has been verified successfully.")
    except CustomUser.DoesNotExist:
        messages.error(request, "Invalid or expired email verification link.")

    return redirect('homepage')
