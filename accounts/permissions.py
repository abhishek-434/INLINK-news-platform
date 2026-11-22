from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme


def get_safe_redirect(request, default='homepage'):
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure()
    ):
        return next_url
    return default


def author_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in to access author tools.")
            return redirect(f"/accounts/login/?next={request.path}")
        if not (request.user.is_author or request.user.is_staff or request.user.is_superuser):
            messages.error(request, "Access restricted. You must be an approved author to access this area.")
            return redirect('author_application')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in with administrator privileges.")
            return redirect(f"/accounts/login/?next={request.path}")
        if not (request.user.is_staff or request.user.is_superuser or request.user.role == 'ADMIN'):
            messages.error(request, "Administrator access required.")
            return redirect('homepage')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
