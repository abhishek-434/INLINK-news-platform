from datetime import timedelta
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden

from accounts.models import CustomUser, AuthorProfile, AuthorApplication
from accounts.permissions import author_required, admin_required
from articles.models import Article, Category, Tag, ArticleReview
from articles.forms import ArticleForm
from reader_features.models import (
    Bookmark, ReadingHistory, AuthorFollow, Comment, ArticleReport, Notification
)
from analytics.models import ArticleView


# ==========================================
# 1. READER DASHBOARD
# ==========================================

@login_required
def reader_overview_view(request):
    user = request.user
    bookmarks_count = Bookmark.objects.filter(user=user).count()
    history_count = ReadingHistory.objects.filter(user=user).count()
    following_count = AuthorFollow.objects.filter(follower=user).count()
    comments_count = Comment.objects.filter(user=user).count()

    recent_history = ReadingHistory.objects.filter(user=user).select_related('article', 'article__category', 'article__author')[:5]
    recent_bookmarks = Bookmark.objects.filter(user=user).select_related('article', 'article__category', 'article__author')[:4]

    return render(request, 'reader_dashboard/overview.html', {
        'bookmarks_count': bookmarks_count,
        'history_count': history_count,
        'following_count': following_count,
        'comments_count': comments_count,
        'recent_history': recent_history,
        'recent_bookmarks': recent_bookmarks,
    })


@login_required
def reader_bookmarks_view(request):
    bookmarks_qs = Bookmark.objects.filter(user=request.user).select_related('article', 'article__category', 'article__author')
    paginator = Paginator(bookmarks_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'reader_dashboard/bookmarks.html', {
        'page_obj': page_obj,
    })


@login_required
def reader_history_view(request):
    if request.method == 'POST' and request.POST.get('action') == 'clear_all':
        ReadingHistory.objects.filter(user=request.user).delete()
        messages.success(request, "Your reading history has been cleared.")
        return redirect('reader_history')

    history_qs = ReadingHistory.objects.filter(user=request.user).select_related('article', 'article__category', 'article__author')
    paginator = Paginator(history_qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'reader_dashboard/history.html', {
        'page_obj': page_obj,
    })


@login_required
def reader_comments_view(request):
    comments_qs = Comment.objects.filter(user=request.user).select_related('article').order_by('-created_at')
    paginator = Paginator(comments_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'reader_dashboard/comments.html', {
        'page_obj': page_obj,
    })


@login_required
def reader_following_view(request):
    following_qs = AuthorFollow.objects.filter(follower=request.user).select_related('author', 'author__author_profile')
    paginator = Paginator(following_qs, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'reader_dashboard/following.html', {
        'page_obj': page_obj,
    })


@login_required
def reader_notifications_view(request):
    if request.method == 'POST' and request.POST.get('action') == 'mark_all_read':
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        messages.success(request, "All notifications marked as read.")
        return redirect('reader_notifications')

    notifications_qs = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    paginator = Paginator(notifications_qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'reader_dashboard/notifications.html', {
        'page_obj': page_obj,
    })


# ==========================================
# 2. AUTHOR DASHBOARD
# ==========================================

@author_required
def author_overview_view(request):
    user = request.user
    my_articles = Article.objects.filter(author=user)

    total_articles = my_articles.count()
    published_count = my_articles.filter(status=Article.ArticleStatus.PUBLISHED).count()
    drafts_count = my_articles.filter(status=Article.ArticleStatus.DRAFT).count()
    pending_count = my_articles.filter(status=Article.ArticleStatus.SUBMITTED).count()
    changes_count = my_articles.filter(status=Article.ArticleStatus.CHANGES_REQUESTED).count()
    rejected_count = my_articles.filter(status=Article.ArticleStatus.REJECTED).count()

    total_views = ArticleView.objects.filter(article__author=user).count()
    recent_articles = my_articles.order_by('-updated_at')[:5]

    followers_count = AuthorFollow.objects.filter(author=user).count()

    return render(request, 'author_dashboard/overview.html', {
        'total_articles': total_articles,
        'published_count': published_count,
        'drafts_count': drafts_count,
        'pending_count': pending_count,
        'changes_count': changes_count,
        'rejected_count': rejected_count,
        'total_views': total_views,
        'followers_count': followers_count,
        'recent_articles': recent_articles,
    })


@author_required
def author_articles_view(request):
    user = request.user
    articles_qs = Article.objects.filter(author=user).select_related('category')

    status_filter = request.GET.get('status')
    if status_filter:
        articles_qs = articles_qs.filter(status=status_filter)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        articles_qs = articles_qs.filter(
            Q(title__icontains=search_query) | Q(excerpt__icontains=search_query)
        )

    articles_qs = articles_qs.order_by('-updated_at')
    paginator = Paginator(articles_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'author_dashboard/my_articles.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'statuses': Article.ArticleStatus.choices,
    })


@author_required
def author_article_create_view(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        action = request.POST.get('action', 'save_draft')

        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user

            if action == 'submit_review':
                article.status = Article.ArticleStatus.SUBMITTED
                msg = "Article successfully submitted for editorial board review."
            else:
                article.status = Article.ArticleStatus.DRAFT
                msg = "Draft article saved successfully."

            article.save()
            form.save_m2m()

            # Record review entry if submitted
            if action == 'submit_review':
                ArticleReview.objects.create(
                    article=article,
                    reviewer=None,
                    action="SUBMITTED",
                    feedback="Author initially submitted story for review."
                )

            messages.success(request, msg)
            return redirect('author_articles')
        else:
            messages.error(request, "Please fix the form errors below.")
    else:
        form = ArticleForm()

    return render(request, 'author_dashboard/article_form.html', {
        'form': form,
        'is_edit': False,
        'title': "Create New Story",
    })


@author_required
def author_article_edit_view(request, pk):
    # Enforce object-level author ownership
    article = get_object_or_404(Article, pk=pk, author=request.user)

    # Initial tag string
    initial_tags = ', '.join([t.name for t in article.tags.all()])

    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article, initial={'tags_input': initial_tags})
        action = request.POST.get('action')

        if form.is_valid():
            updated_article = form.save(commit=False)

            # Publishing restriction: Authors cannot self-publish.
            # If an already published article is updated, it must be returned to SUBMITTED for editorial re-approval.
            if article.status == Article.ArticleStatus.PUBLISHED:
                if action == 'submit_review':
                    updated_article.status = Article.ArticleStatus.SUBMITTED
                    msg = "Published article updated and resubmitted for editorial re-review."
                else:
                    updated_article.status = Article.ArticleStatus.DRAFT
                    msg = "Changes saved as draft (article taken offline until re-submitted and approved)."
            elif action == 'submit_review':
                updated_article.status = Article.ArticleStatus.SUBMITTED
                msg = "Article successfully submitted for editorial review."
            else:
                # Keep current status if it's draft or changes requested
                if updated_article.status not in [Article.ArticleStatus.DRAFT, Article.ArticleStatus.CHANGES_REQUESTED]:
                    updated_article.status = Article.ArticleStatus.DRAFT
                msg = "Draft updated successfully."

            updated_article.save()
            form.save_m2m()

            if action == 'submit_review':
                ArticleReview.objects.create(
                    article=updated_article,
                    reviewer=None,
                    action="RESUBMITTED",
                    feedback="Author resubmitted revised story."
                )

            messages.success(request, msg)
            return redirect('author_articles')
        else:
            messages.error(request, "Please correct the form errors.")
    else:
        form = ArticleForm(instance=article, initial={'tags_input': initial_tags})

    recent_reviews = article.reviews.all().order_by('-created_at')[:5]

    return render(request, 'author_dashboard/article_form.html', {
        'form': form,
        'article': article,
        'is_edit': True,
        'recent_reviews': recent_reviews,
        'title': f"Edit Story: {article.title}",
    })


@author_required
def author_article_delete_view(request, pk):
    article = get_object_or_404(Article, pk=pk, author=request.user)

    # Only drafts or rejected articles can be deleted directly by author
    if article.status in [Article.ArticleStatus.DRAFT, Article.ArticleStatus.REJECTED]:
        if request.method == 'POST':
            article.delete()
            messages.success(request, "Article draft deleted.")
            return redirect('author_articles')
        return render(request, 'author_dashboard/confirm_delete.html', {'article': article})
    else:
        messages.error(request, "Submitted or published articles cannot be deleted directly. Contact an administrator.")
        return redirect('author_articles')


# ==========================================
# 3. ADMINISTRATOR DASHBOARD
# ==========================================

@admin_required
def admin_overview_view(request):
    total_users = CustomUser.objects.count()
    total_authors = CustomUser.objects.filter(role=CustomUser.Role.AUTHOR).count()
    pending_author_apps = AuthorApplication.objects.filter(status=AuthorApplication.Status.PENDING).count()

    total_articles = Article.objects.count()
    pending_articles = Article.objects.filter(status=Article.ArticleStatus.SUBMITTED).count()
    published_articles = Article.objects.filter(status=Article.ArticleStatus.PUBLISHED).count()

    total_comments = Comment.objects.count()
    pending_reports = ArticleReport.objects.filter(is_resolved=False).count()

    # Chart 1: Article Views over the past 7 days
    now = timezone.now()
    labels_views = []
    data_views = []
    for i in range(6, -1, -1):
        day = (now - timedelta(days=i)).date()
        count = ArticleView.objects.filter(timestamp__date=day).count()
        labels_views.append(day.strftime("%b %d"))
        data_views.append(count)

    # Chart 2: Articles per category
    category_counts = Category.objects.annotate(
        art_count=Count('articles', filter=Q(articles__status=Article.ArticleStatus.PUBLISHED))
    ).order_by('-art_count')[:6]
    labels_categories = [c.name for c in category_counts]
    data_categories = [c.art_count for c in category_counts]

    # Chart 3: Article Status Breakdown
    status_counts = Article.objects.values('status').annotate(count=Count('id'))
    status_map = {item['status']: item['count'] for item in status_counts}
    labels_status = ['Published', 'Pending Review', 'Drafts', 'Rejected']
    data_status = [
        status_map.get(Article.ArticleStatus.PUBLISHED, 0),
        status_map.get(Article.ArticleStatus.SUBMITTED, 0),
        status_map.get(Article.ArticleStatus.DRAFT, 0),
        status_map.get(Article.ArticleStatus.REJECTED, 0),
    ]

    recent_submissions = Article.objects.filter(
        status=Article.ArticleStatus.SUBMITTED
    ).select_related('author', 'category').order_by('-updated_at')[:5]

    recent_applications = AuthorApplication.objects.filter(
        status=AuthorApplication.Status.PENDING
    ).select_related('user').order_by('-created_at')[:5]

    return render(request, 'admin_dashboard/overview.html', {
        'total_users': total_users,
        'total_authors': total_authors,
        'pending_author_apps': pending_author_apps,
        'total_articles': total_articles,
        'pending_articles': pending_articles,
        'published_articles': published_articles,
        'total_comments': total_comments,
        'pending_reports': pending_reports,
        'recent_submissions': recent_submissions,
        'recent_applications': recent_applications,
        # JSON metrics for Chart.js
        'labels_views_json': json.dumps(labels_views),
        'data_views_json': json.dumps(data_views),
        'labels_categories_json': json.dumps(labels_categories),
        'data_categories_json': json.dumps(data_categories),
        'labels_status_json': json.dumps(labels_status),
        'data_status_json': json.dumps(data_status),
    })


@admin_required
def admin_review_queue_view(request):
    submissions = Article.objects.filter(
        status=Article.ArticleStatus.SUBMITTED
    ).select_related('author', 'category').order_by('-updated_at')

    paginator = Paginator(submissions, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'admin_dashboard/articles_review.html', {
        'page_obj': page_obj,
    })


@admin_required
def admin_review_detail_view(request, pk):
    article = get_object_or_404(
        Article.objects.select_related('author', 'category', 'author__author_profile'),
        pk=pk
    )

    if request.method == 'POST':
        action = request.POST.get('action')
        feedback = request.POST.get('feedback', '').strip()

        if action == 'approve_publish':
            article.status = Article.ArticleStatus.PUBLISHED
            article.published_at = timezone.now()
            article.save()
            ArticleReview.objects.create(
                article=article,
                reviewer=request.user,
                action="APPROVED & PUBLISHED",
                feedback=feedback or "Approved for immediate publication."
            )
            Notification.objects.create(
                recipient=article.author,
                title="Your story has been published!",
                message=f"Congratulations! '{article.title}' is now live on INKLINE.",
                link=f"/articles/{article.slug}/"
            )
            messages.success(request, f"Article '{article.title}' has been approved and published.")
            return redirect('admin_review_queue')

        elif action == 'request_changes':
            if not feedback:
                messages.error(request, "Please provide feedback explaining what changes are needed.")
                return render(request, 'admin_dashboard/article_detail_review.html', {'article': article})

            article.status = Article.ArticleStatus.CHANGES_REQUESTED
            article.save()
            ArticleReview.objects.create(
                article=article,
                reviewer=request.user,
                action="CHANGES REQUESTED",
                feedback=feedback
            )
            Notification.objects.create(
                recipient=article.author,
                title="Changes requested for your article",
                message=f"The editorial board requested revisions on '{article.title}': {feedback[:120]}...",
                link=f"/dashboard/author/articles/{article.id}/edit/"
            )
            messages.warning(request, f"Revisions requested for '{article.title}'. Author notified.")
            return redirect('admin_review_queue')

        elif action == 'reject':
            if not feedback:
                messages.error(request, "Please state the reason for rejecting this article.")
                return render(request, 'admin_dashboard/article_detail_review.html', {'article': article})

            article.status = Article.ArticleStatus.REJECTED
            article.save()
            ArticleReview.objects.create(
                article=article,
                reviewer=request.user,
                action="REJECTED",
                feedback=feedback
            )
            Notification.objects.create(
                recipient=article.author,
                title="Article review status: Rejected",
                message=f"Your submission '{article.title}' was rejected by the editorial board: {feedback[:120]}...",
                link=f"/dashboard/author/articles/{article.id}/edit/"
            )
            messages.error(request, f"Article '{article.title}' has been rejected.")
            return redirect('admin_review_queue')

    reviews = article.reviews.all().order_by('-created_at')

    return render(request, 'admin_dashboard/article_detail_review.html', {
        'article': article,
        'reviews': reviews,
    })


@admin_required
def admin_all_articles_view(request):
    articles_qs = Article.objects.all().select_related('author', 'category').order_by('-created_at')

    status_filter = request.GET.get('status')
    if status_filter:
        articles_qs = articles_qs.filter(status=status_filter)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        articles_qs = articles_qs.filter(
            Q(title__icontains=search_query) | Q(author__username__icontains=search_query)
        )

    paginator = Paginator(articles_qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'admin_dashboard/all_articles.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'statuses': Article.ArticleStatus.choices,
    })


@admin_required
def admin_article_toggle_feature_view(request, pk):
    article = get_object_or_404(Article, pk=pk)
    feature_type = request.POST.get('type')

    if feature_type == 'hero':
        article.is_featured = not article.is_featured
        article.save()
        messages.success(request, f"Featured hero status updated for '{article.title}'.")
    elif feature_type == 'editors_pick':
        article.is_editors_pick = not article.is_editors_pick
        article.save()
        messages.success(request, f"Editor's Pick status updated for '{article.title}'.")
    elif feature_type == 'archive':
        article.status = Article.ArticleStatus.ARCHIVED
        article.save()
        messages.info(request, f"Article '{article.title}' archived.")

    return redirect(request.META.get('HTTP_REFERER', 'admin_all_articles'))


@admin_required
def admin_authors_view(request):
    # Tab 1: Author Applications
    applications = AuthorApplication.objects.select_related('user').order_by('-created_at')
    # Tab 2: Approved Authors
    authors = CustomUser.objects.filter(role=CustomUser.Role.AUTHOR).select_related('author_profile').annotate(
        pub_count=Count('articles', filter=Q(articles__status=Article.ArticleStatus.PUBLISHED))
    ).order_by('-date_joined')

    return render(request, 'admin_dashboard/authors_management.html', {
        'applications': applications,
        'authors': authors,
    })


@admin_required
def admin_review_author_application_view(request, pk):
    app = get_object_or_404(AuthorApplication, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        admin_notes = request.POST.get('admin_notes', '').strip()

        if action == 'approve':
            app.status = AuthorApplication.Status.APPROVED
            app.admin_notes = admin_notes
            app.reviewed_by = request.user
            app.reviewed_at = timezone.now()
            app.save()

            # Elevate user to AUTHOR role
            user = app.user
            user.role = CustomUser.Role.AUTHOR
            user.save()

            # Create or update AuthorProfile
            profile, _ = AuthorProfile.objects.get_or_create(user=user)
            profile.pen_name = app.full_name
            profile.bio = app.bio
            profile.writing_interests = app.writing_interests
            if app.profile_picture:
                profile.profile_picture = app.profile_picture
            profile.is_approved = True
            profile.approved_at = timezone.now()
            profile.save()

            Notification.objects.create(
                recipient=user,
                title="Welcome to the INKLINE Newsroom!",
                message="Your author application has been approved! You can now compose and submit stories.",
                link="/dashboard/author/"
            )

            messages.success(request, f"Application for {app.full_name} approved. Author privileges granted.")
            return redirect('admin_authors')

        elif action == 'reject':
            app.status = AuthorApplication.Status.REJECTED
            app.admin_notes = admin_notes or "Did not meet editorial criteria at this time."
            app.reviewed_by = request.user
            app.reviewed_at = timezone.now()
            app.save()

            Notification.objects.create(
                recipient=app.user,
                title="Author Application Status Update",
                message=f"Your author application was not approved: {app.admin_notes}",
                link="/accounts/author-application/status/"
            )

            messages.warning(request, f"Application for {app.full_name} rejected.")
            return redirect('admin_authors')

    return render(request, 'admin_dashboard/author_application_detail.html', {'app': app})


@admin_required
def admin_toggle_author_suspension_view(request, user_id):
    author_user = get_object_or_404(CustomUser, id=user_id)
    if hasattr(author_user, 'author_profile'):
        profile = author_user.author_profile
        profile.is_suspended = not profile.is_suspended
        profile.save()
        status_txt = "suspended" if profile.is_suspended else "reactivated"
        messages.warning(request, f"Author {author_user.username} has been {status_txt}.")

    return redirect('admin_authors')


@admin_required
def admin_readers_view(request):
    readers_qs = CustomUser.objects.filter(role=CustomUser.Role.READER).annotate(
        read_count=Count('reading_history'),
        bookmark_count=Count('bookmarks'),
        comment_count=Count('article_comments')
    ).order_by('-date_joined')

    search = request.GET.get('q', '').strip()
    if search:
        readers_qs = readers_qs.filter(
            Q(username__icontains=search) | Q(email__icontains=search) | Q(first_name__icontains=search)
        )

    paginator = Paginator(readers_qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'admin_dashboard/readers_management.html', {
        'page_obj': page_obj,
    })


@admin_required
def admin_toggle_user_active_view(request, user_id):
    target_user = get_object_or_404(CustomUser, id=user_id)
    if target_user.is_superuser:
        messages.error(request, "Superuser accounts cannot be deactivated here.")
        return redirect('admin_readers')

    target_user.is_active = not target_user.is_active
    target_user.save()
    status_str = "activated" if target_user.is_active else "deactivated"
    messages.success(request, f"User {target_user.username} has been {status_str}.")
    return redirect('admin_readers')


@admin_required
def admin_content_moderation_view(request):
    # Comments moderation
    comments = Comment.objects.select_related('user', 'article').order_by('-created_at')[:20]

    # Reports moderation
    reports = ArticleReport.objects.select_related('article', 'reported_by').order_by('-created_at')[:20]

    # Categories list
    categories = Category.objects.annotate(total_articles=Count('articles')).order_by('order', 'name')

    return render(request, 'admin_dashboard/content_management.html', {
        'comments': comments,
        'reports': reports,
        'categories': categories,
    })


@admin_required
def admin_resolve_report_view(request, report_id):
    report = get_object_or_404(ArticleReport, id=report_id)
    report.is_resolved = True
    report.resolved_by = request.user
    report.resolution_notes = request.POST.get('resolution_notes', 'Moderated and marked as resolved.')
    report.save()
    messages.success(request, "Report marked as resolved.")
    return redirect('admin_content_moderation')


@admin_required
def admin_analytics_view(request):
    # Deep analytics
    now = timezone.now()
    labels_views = []
    data_views = []
    for i in range(13, -1, -1):
        day = (now - timedelta(days=i)).date()
        count = ArticleView.objects.filter(timestamp__date=day).count()
        labels_views.append(day.strftime("%b %d"))
        data_views.append(count)

    top_articles = Article.objects.filter(status=Article.ArticleStatus.PUBLISHED).order_by('-views_count')[:8]
    top_authors = CustomUser.objects.filter(role=CustomUser.Role.AUTHOR).annotate(
        total_views=Sum('articles__views_count')
    ).order_by('-total_views')[:6]

    return render(request, 'admin_dashboard/analytics.html', {
        'labels_views_json': json.dumps(labels_views),
        'data_views_json': json.dumps(data_views),
        'top_articles': top_articles,
        'top_authors': top_authors,
    })
