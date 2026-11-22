from reader_features.models import Notification


def user_notifications_count(request):
    if request.user.is_authenticated:
        try:
            unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        except Exception:
            unread_count = 0
        return {'unread_notifications_count': unread_count}
    return {'unread_notifications_count': 0}
