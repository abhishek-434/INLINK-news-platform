from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('author-application/', views.author_application_view, name='author_application'),
    path('author-application/status/', views.author_application_status_view, name='author_application_status'),
    path('settings/', views.profile_settings_view, name='profile_settings'),
    path('verify-email/<str:token>/', views.verify_email_view, name='verify_email'),
]
