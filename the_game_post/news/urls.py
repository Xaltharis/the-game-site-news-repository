from django.urls import path
from django.contrib.auth import views as auth_views
from .views import *

app_name = 'news'

urlpatterns = [
    path('', article_list, name='article_list'),
    path('category/<slug:category_slug>/', article_list, name='articles_by_category'),
    path('article/<slug:slug>/', article_detail, name='article_detail'),
    path('tag/<slug:tag_slug>/', articles_by_tag, name='articles_by_tag'),
    path('article/<slug:slug>/comment/', add_comment, name='add_comment'),
    path('comment/<int:comment_id>/delete/', delete_comment, name='delete_comment'),
    path('about/', about, name='about'),

    # Авторизация
    path('register/', register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='news/login.html'), name='login'),
    path('logout/', custom_logout, name='logout'),
]