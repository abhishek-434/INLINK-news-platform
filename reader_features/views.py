from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import bleach
from .models import Bookmark, Comment, ArticleReport, AuthorFollow, Notification
from articles.models import Article
from accounts.models import CustomUser


@login_required
@require_POST
def toggle_bookmark_view(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    bookmark, created = Bookmark.objects.get_or_create(user=request.user, article=article)

    if not created:
        bookmark.delete()
        bookmarked = False
        msg = f"Removed '{article.title}' from your bookmarks."
    else:
        bookmarked = True
        msg = f"Saved '{article.title}' to your bookmarks."

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'bookmarked': bookmarked, 'message': msg})

    messages.success(request, msg)
    return redirect(request.META.get('HTTP_REFERER', 'homepage'))


@login_required
@require_POST
def add_comment_view(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    content = request.POST.get('content', '').strip()
    parent_id = request.POST.get('parent_id')

    if not content:
        messages.error(request, "Comment cannot be empty.")
        return redirect(article.get_absolute_url() if hasattr(article, 'get_absolute_url') else f"/articles/{article.slug}/")

    # Sanitize comment (strip script tags completely)
    import re
    cleaned = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', content, flags=re.DOTALL | re.IGNORECASE)
    safe_content = bleach.clean(cleaned, tags=[], strip=True)

    parent_comment = None
    if parent_id:
        parent_comment = Comment.objects.filter(id=parent_id, article=article).first()

    comment = Comment.objects.create(
        article=article,
        user=request.user,
        parent=parent_comment,
        content=safe_content,
        is_approved=True
    )

    # Notify article author if commenter is not the author
    if article.author != request.user:
        Notification.objects.create(
            recipient=article.author,
            title=f"New comment on '{article.title}'",
            message=f"{request.user.username} commented on your article: '{safe_content[:100]}...'",
            link=f"/articles/{article.slug}/#comment-{comment.id}"
        )

    messages.success(request, "Your comment has been published.")
    return redirect(f"/articles/{article.slug}/#comment-{comment.id}")


@login_required
@require_POST
def edit_comment_view(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, user=request.user)
    new_content = request.POST.get('content', '').strip()

    if new_content:
        comment.content = bleach.clean(new_content, tags=[], strip=True)
        comment.save()
        messages.success(request, "Comment updated successfully.")
    else:
        messages.error(request, "Comment cannot be empty.")

    return redirect(f"/articles/{comment.article.slug}/#comment-{comment.id}")


@login_required
@require_POST
def delete_comment_view(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    article_slug = comment.article.slug

    # Only author of comment or staff can delete
    if comment.user == request.user or request.user.is_staff or request.user.role == 'ADMIN':
        comment.delete()
        messages.success(request, "Comment has been deleted.")
    else:
        messages.error(request, "You do not have permission to delete this comment.")

    return redirect(f"/articles/{article_slug}/#comments")


@login_required
@require_POST
def report_article_view(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    reason = request.POST.get('reason', ArticleReport.Reason.OTHER)
    details = request.POST.get('details', '').strip()

    if not details:
        messages.error(request, "Please provide details explaining why you are reporting this article.")
        return redirect(f"/articles/{article.slug}/")

    ArticleReport.objects.create(
        article=article,
        reported_by=request.user,
        reason=reason,
        details=bleach.clean(details, tags=[], strip=True)
    )

    messages.success(
        request,
        "Thank you. Your report has been submitted to the editorial review team for moderation."
    )
    return redirect(f"/articles/{article.slug}/")


@login_required
@require_POST
def toggle_follow_author_view(request, author_id):
    author = get_object_or_404(CustomUser, id=author_id)
    if author == request.user:
        messages.warning(request, "You cannot follow yourself.")
        return redirect(request.META.get('HTTP_REFERER', 'homepage'))

    follow, created = AuthorFollow.objects.get_or_create(follower=request.user, author=author)
    if not created:
        follow.delete()
        is_following = False
        msg = f"You are no longer following {author.first_name or author.username}."
    else:
        is_following = True
        msg = f"You are now following {author.first_name or author.username}."
        Notification.objects.create(
            recipient=author,
            title="New Follower",
            message=f"{request.user.username} started following your stories.",
            link=f"/authors/{request.user.username}/"
        )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'is_following': is_following, 'message': msg})

    messages.success(request, msg)
    return redirect(request.META.get('HTTP_REFERER', 'homepage'))


@login_required
def mark_notification_read_view(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    if notification.link:
        return redirect(notification.link)
    return redirect('reader_notifications')
