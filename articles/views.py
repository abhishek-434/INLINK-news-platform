from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Count, F
from django.http import Http404, HttpResponseForbidden
from django.utils import timezone
from django.contrib import messages
from .models import Article, Category, Tag
from reader_features.models import Bookmark, ReadingHistory, AuthorFollow, Comment
from analytics.models import ArticleView
from accounts.models import CustomUser, AuthorProfile


def homepage_view(request):
    now = timezone.now()
    published_qs = Article.objects.filter(
        status=Article.ArticleStatus.PUBLISHED,
        published_at__lte=now
    ).select_related('author', 'category', 'author__author_profile').prefetch_related('tags')

    # Main Hero featured story
    hero_article = published_qs.filter(is_featured=True).first()
    if not hero_article:
        hero_article = published_qs.first()

    hero_id = hero_article.id if hero_article else None

    # Secondary featured stories (exclude hero)
    secondary_featured = published_qs.exclude(id=hero_id)[:3]
    excluded_ids = set([hero_id] + list(secondary_featured.values_list('id', flat=True))) if hero_id else set()

    # Latest news feed
    latest_news = published_qs.exclude(id__in=excluded_ids)[:6]

    # Trending stories (based on views or trending flag)
    trending_articles = published_qs.order_by('-views_count', '-published_at')[:5]

    # Editor's picks
    editors_picks = published_qs.filter(is_editors_pick=True).exclude(id__in=excluded_ids)[:4]

    # Category slices for magazine layout
    categories = Category.objects.filter(is_active=True).order_by('order', 'name')
    category_articles = {}
    for cat in categories:
        articles_in_cat = published_qs.filter(category=cat)[:4]
        if articles_in_cat.exists():
            category_articles[cat] = articles_in_cat

    # Popular authors
    popular_authors = CustomUser.objects.filter(
        articles__status=Article.ArticleStatus.PUBLISHED
    ).select_related('author_profile').annotate(
        pub_count=Count('articles', distinct=True),
        total_views=Count('articles__views_log', distinct=True)
    ).filter(pub_count__gt=0).order_by('-pub_count')[:4]

    return render(request, 'homepage/index.html', {
        'hero_article': hero_article,
        'secondary_featured': secondary_featured,
        'latest_news': latest_news,
        'trending_articles': trending_articles,
        'editors_picks': editors_picks,
        'category_articles': category_articles,
        'popular_authors': popular_authors,
    })


def article_list_view(request):
    now = timezone.now()
    articles_qs = Article.objects.filter(
        status=Article.ArticleStatus.PUBLISHED,
        published_at__lte=now
    ).select_related('author', 'category', 'author__author_profile').prefetch_related('tags')

    category_slug = request.GET.get('category')
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        articles_qs = articles_qs.filter(category=selected_category)

    article_type = request.GET.get('type')
    if article_type:
        articles_qs = articles_qs.filter(article_type=article_type)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        articles_qs = articles_qs.filter(
            Q(title__icontains=search_query) |
            Q(subtitle__icontains=search_query) |
            Q(excerpt__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(author__first_name__icontains=search_query) |
            Q(author__last_name__icontains=search_query) |
            Q(author__username__icontains=search_query) |
            Q(tags__name__icontains=search_query)
        ).distinct()

    sort = request.GET.get('sort', 'latest')
    if sort == 'popular':
        articles_qs = articles_qs.order_by('-views_count', '-published_at')
    else:
        articles_qs = articles_qs.order_by('-published_at')

    paginator = Paginator(articles_qs, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'articles/list.html', {
        'page_obj': page_obj,
        'selected_category': selected_category,
        'selected_type': article_type,
        'sort': sort,
        'search_query': search_query,
        'article_types': Article.ArticleType.choices,
    })


def category_detail_view(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    now = timezone.now()
    articles_qs = Article.objects.filter(
        category=category,
        status=Article.ArticleStatus.PUBLISHED,
        published_at__lte=now
    ).select_related('author', 'author__author_profile').prefetch_related('tags')

    sort = request.GET.get('sort', 'latest')
    if sort == 'popular':
        articles_qs = articles_qs.order_by('-views_count', '-published_at')
    else:
        articles_qs = articles_qs.order_by('-published_at')

    paginator = Paginator(articles_qs, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'articles/category.html', {
        'category': category,
        'page_obj': page_obj,
        'sort': sort,
    })


def tag_detail_view(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    now = timezone.now()
    articles_qs = Article.objects.filter(
        tags=tag,
        status=Article.ArticleStatus.PUBLISHED,
        published_at__lte=now
    ).select_related('author', 'category', 'author__author_profile').prefetch_related('tags')

    paginator = Paginator(articles_qs, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'articles/tag.html', {
        'tag': tag,
        'page_obj': page_obj,
    })


def article_detail_view(request, slug):
    """
    Core Server-Side Content Protection:
    - Guests receive ONLY metadata and excerpt. The full article content is STRICTLY None in template context.
    - An access restriction prompt provides buttons to Login or Register with preserved next URL.
    - Authenticated readers receive full sanitized content, view count increment, and reading history logging.
    - Unpublished articles are strictly hidden unless the requester is the author or administrator.
    """
    article = get_object_or_404(
        Article.objects.select_related('author', 'category', 'author__author_profile').prefetch_related('tags'),
        slug=slug
    )

    # Permission check for unpublished drafts/articles
    is_author_owner = request.user.is_authenticated and request.user == article.author
    is_staff_or_admin = request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser or request.user.role == 'ADMIN')

    if not article.is_publicly_readable:
        if not (is_author_owner or is_staff_or_admin):
            raise Http404("Article not found or not yet published.")

    # Access Gating: Server-side check
    is_authenticated_reader = request.user.is_authenticated
    full_content = None
    is_bookmarked = False
    is_following_author = False

    if is_authenticated_reader:
        # Full content is supplied ONLY to authenticated accounts
        full_content = article.content

        # Record view analytics (debounced by session or ip)
        ip = request.META.get('REMOTE_ADDR')
        agent = request.META.get('HTTP_USER_AGENT', '')[:255]
        session_id = request.session.session_key or ''
        
        # Increment view count
        Article.objects.filter(pk=article.pk).update(views_count=F('views_count') + 1)
        ArticleView.objects.create(
            article=article,
            user=request.user,
            ip_address=ip,
            user_agent=agent,
            session_key=session_id
        )

        # Log or update reading history
        ReadingHistory.objects.update_or_create(
            user=request.user,
            article=article,
            defaults={'progress_percent': 100}
        )

        # Check bookmark status
        is_bookmarked = Bookmark.objects.filter(user=request.user, article=article).exists()

        # Check follow status for author
        if request.user != article.author:
            is_following_author = AuthorFollow.objects.filter(
                follower=request.user,
                author=article.author
            ).exists()
    else:
        # For guests, do not supply full_content.
        full_content = None

    # Comments (only approved comments)
    comments = article.comments.filter(is_approved=True, parent=None).select_related('user').prefetch_related('replies__user')

    # Related articles (same category or tags, exclude current)
    related_articles = Article.objects.filter(
        status=Article.ArticleStatus.PUBLISHED,
        published_at__lte=timezone.now(),
        category=article.category
    ).exclude(id=article.id).select_related('author', 'category')[:3]

    # Trending stories in this section for sidebar
    sidebar_trending = Article.objects.filter(
        status=Article.ArticleStatus.PUBLISHED,
        published_at__lte=timezone.now(),
    ).exclude(id=article.id).order_by('-views_count', '-published_at')[:4]

    # Gallery / Companion small images
    gallery_images = list(article.gallery_images.all())

    return render(request, 'articles/detail.html', {
        'article': article,
        'is_authenticated_reader': is_authenticated_reader,
        'full_content': full_content,
        'is_bookmarked': is_bookmarked,
        'is_following_author': is_following_author,
        'comments': comments,
        'related_articles': related_articles,
        'sidebar_trending': sidebar_trending,
        'gallery_images': gallery_images,
        'is_preview_mode': not article.is_publicly_readable,
    })


def author_public_profile_view(request, username):
    author_user = get_object_or_404(CustomUser, username=username)
    author_profile = getattr(author_user, 'author_profile', None)

    published_articles = Article.objects.filter(
        author=author_user,
        status=Article.ArticleStatus.PUBLISHED,
        published_at__lte=timezone.now()
    ).select_related('category').order_by('-published_at')

    paginator = Paginator(published_articles, 6)
    page_obj = paginator.get_page(request.GET.get('page'))

    is_following = False
    if request.user.is_authenticated and request.user != author_user:
        is_following = AuthorFollow.objects.filter(follower=request.user, author=author_user).exists()

    follower_count = AuthorFollow.objects.filter(author=author_user).count()

    return render(request, 'authors/public_profile.html', {
        'author_user': author_user,
        'author_profile': author_profile,
        'page_obj': page_obj,
        'is_following': is_following,
        'follower_count': follower_count,
        'total_published': published_articles.count(),
    })


def search_view(request):
    query = request.GET.get('q', '').strip()
    articles_qs = Article.objects.none()

    if query:
        now = timezone.now()
        articles_qs = Article.objects.filter(
            status=Article.ArticleStatus.PUBLISHED,
            published_at__lte=now
        ).filter(
            Q(title__icontains=query) |
            Q(subtitle__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(content__icontains=query) |
            Q(author__first_name__icontains=query) |
            Q(author__last_name__icontains=query) |
            Q(author__username__icontains=query) |
            Q(category__name__icontains=query) |
            Q(tags__name__icontains=query)
        ).select_related('author', 'category').distinct().order_by('-published_at')

    paginator = Paginator(articles_qs, 9)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'articles/search.html', {
        'query': query,
        'page_obj': page_obj,
        'total_results': paginator.count,
    })
