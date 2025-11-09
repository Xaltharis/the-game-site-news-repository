from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'news'

urlpatterns = [
    path('', views.article_list, name='article_list'),
    path('article/<slug:slug>/', views.article_detail, name='article_detail'),
    path('tag/<slug:tag_slug>/', views.articles_by_tag, name='articles_by_tag'),
    path('article/<slug:slug>/comment/', views.add_comment, name='add_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='news/login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),
]