from django.urls import path
from . import views

urlpatterns = [
    path('', views.article_list_view, name='article_list'),
    path('search/', views.search_view, name='search'),
    path('category/<slug:slug>/', views.category_detail_view, name='category_detail'),
    path('tag/<slug:slug>/', views.tag_detail_view, name='tag_detail'),
    path('author/<str:username>/', views.author_public_profile_view, name='author_public_profile'),
    path('<slug:slug>/', views.article_detail_view, name='article_detail'),
]
