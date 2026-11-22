from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import NewsletterSubscription


@require_POST
def subscribe_newsletter_view(request):
    email = request.POST.get('email', '').strip().lower()

    if not email:
        msg = "Please provide a valid email address."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': msg}, status=400)
        messages.error(request, msg)
        return redirect(request.META.get('HTTP_REFERER', 'homepage'))

    try:
        validate_email(email)
    except ValidationError:
        msg = "The email address provided is not valid."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': msg}, status=400)
        messages.error(request, msg)
        return redirect(request.META.get('HTTP_REFERER', 'homepage'))

    subscription, created = NewsletterSubscription.objects.get_or_create(
        email=email,
        defaults={'is_active': True}
    )

    if not created and not subscription.is_active:
        subscription.is_active = True
        subscription.save()

    msg = "Thank you for subscribing to INKLINE's daily editorial dispatch."
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'message': msg})

    messages.success(request, msg)
    return redirect(request.META.get('HTTP_REFERER', 'homepage'))
