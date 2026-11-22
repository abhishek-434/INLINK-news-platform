from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from articles.views import homepage_view


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /dashboard/",
        "Disallow: /accounts/",
        "Allow: /",
        "Sitemap: " + request.build_absolute_uri('/sitemap.xml'),
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def sitemap_xml(request):
    from articles.models import Article
    from django.utils import timezone
    articles = Article.objects.filter(
        status=Article.ArticleStatus.PUBLISHED,
        published_at__lte=timezone.now()
    ).order_by('-published_at')[:100]

    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    xml.append(f'  <url><loc>{request.build_absolute_uri("/")}</loc><priority>1.0</priority></url>')
    xml.append(f'  <url><loc>{request.build_absolute_uri("/articles/")}</loc><priority>0.9</priority></url>')
    for a in articles:
        xml.append(f'  <url><loc>{request.build_absolute_uri(f"/articles/{a.slug}/")}</loc><lastmod>{a.updated_at.strftime("%Y-%m-%d")}</lastmod><priority>0.8</priority></url>')
    xml.append('</urlset>')
    return HttpResponse("\n".join(xml), content_type="application/xml")


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', homepage_view, name='homepage'),
    path('accounts/', include('accounts.urls')),
    path('articles/', include('articles.urls')),
    path('features/', include('reader_features.urls')),
    path('newsletter/', include('newsletter.urls')),
    path('dashboard/', include('dashboards.urls')),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap_xml, name='sitemap_xml'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
