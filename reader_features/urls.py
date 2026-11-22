from django.urls import path
from . import views

urlpatterns = [
    path('bookmark/<int:article_id>/', views.toggle_bookmark_view, name='toggle_bookmark'),
    path('comment/<int:article_id>/', views.add_comment_view, name='add_comment'),
    path('comment/edit/<int:comment_id>/', views.edit_comment_view, name='edit_comment'),
    path('comment/delete/<int:comment_id>/', views.delete_comment_view, name='delete_comment'),
    path('report/<int:article_id>/', views.report_article_view, name='report_article'),
    path('follow/<int:author_id>/', views.toggle_follow_author_view, name='toggle_follow_author'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read_view, name='mark_notification_read'),
]
