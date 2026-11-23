from django.urls import path
from . import views

urlpatterns = [
    # Reader Dashboard
    path('reader/', views.reader_overview_view, name='reader_overview'),
    path('reader/bookmarks/', views.reader_bookmarks_view, name='reader_bookmarks'),
    path('reader/history/', views.reader_history_view, name='reader_history'),
    path('reader/comments/', views.reader_comments_view, name='reader_comments'),
    path('reader/following/', views.reader_following_view, name='reader_following'),
    path('reader/notifications/', views.reader_notifications_view, name='reader_notifications'),

    # Author Dashboard
    path('author/', views.author_overview_view, name='author_overview'),
    path('author/articles/', views.author_articles_view, name='author_articles'),
    path('author/articles/create/', views.author_article_create_view, name='author_article_create'),
    path('author/articles/<int:pk>/edit/', views.author_article_edit_view, name='author_article_edit'),
    path('author/articles/<int:pk>/delete/', views.author_article_delete_view, name='author_article_delete'),

    # Admin Dashboard
    path('admin-portal/', views.admin_overview_view, name='admin_overview'),
    path('admin-portal/reviews/', views.admin_review_queue_view, name='admin_review_queue'),
    path('admin-portal/reviews/<int:pk>/', views.admin_review_detail_view, name='admin_review_detail'),
    path('admin-portal/reviews/<int:pk>/quick-approve/', views.admin_quick_approve_view, name='admin_quick_approve'),
    path('admin-portal/articles/', views.admin_all_articles_view, name='admin_all_articles'),
    path('admin-portal/articles/<int:pk>/toggle-feature/', views.admin_article_toggle_feature_view, name='admin_article_toggle_feature'),
    path('admin-portal/authors/', views.admin_authors_view, name='admin_authors'),
    path('admin-portal/authors/applications/<int:pk>/', views.admin_review_author_application_view, name='admin_review_author_application'),
    path('admin-portal/authors/<int:user_id>/toggle-suspend/', views.admin_toggle_author_suspension_view, name='admin_toggle_author_suspension'),
    path('admin-portal/readers/', views.admin_readers_view, name='admin_readers'),
    path('admin-portal/readers/<int:user_id>/toggle-active/', views.admin_toggle_user_active_view, name='admin_toggle_user_active'),
    path('admin-portal/content/', views.admin_content_moderation_view, name='admin_content_moderation'),
    path('admin-portal/reports/<int:report_id>/resolve/', views.admin_resolve_report_view, name='admin_resolve_report'),
    path('admin-portal/analytics/', views.admin_analytics_view, name='admin_analytics'),
]
