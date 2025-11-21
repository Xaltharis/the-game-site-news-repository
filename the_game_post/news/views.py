from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from datetime import timedelta
from .models import Article, Tag, Comment, Category, Genre
from .forms import CommentForm, RegisterForm


def register(request):
    """Регистрация пользователя"""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('news:article_list')
    else:
        form = RegisterForm()
    
    context = get_common_context()
    context['form'] = form
    return render(request, 'news/register.html', context)


def custom_login(request):
    from django.contrib.auth import authenticate, login
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Вы успешно вошли!')
            return redirect('news:article_list')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    
    context = get_common_context()
    return render(request, 'news/login.html', context)


def custom_logout(request):
    """Выход пользователя"""
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы!')
    return redirect('news:article_list')


def get_common_context():
    """Возвращает общий контекст для нескольких представлений"""
    return {
        'all_tags': Tag.objects.all(),
        'all_genres': Genre.objects.all()  # Добавляем жанры
    }


def article_list(request, category_slug=None):
    articles_list = Article.objects.filter(is_published=True)
    
    # Фильтрация по категории
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        articles_list = articles_list.filter(category=category)
        current_category = category
        show_hero = False  # Не показываем hero на категориях
    else:
        current_category = None
        show_hero = True   # Показываем hero только на "Все новости"
    
    # Получаем статьи для Hero блока (только для главной)
    hero_articles = []
    if show_hero:
        # 1. Самые просматриваемые за все время (3 статьи)
        most_viewed = articles_list.order_by('-views')[:3]
        
        # 2. За последнюю неделю (по дате создания)
        week_ago = timezone.now() - timedelta(days=7)
        recent_popular = articles_list.filter(
            created_at__gte=week_ago
        ).order_by('-views')[:3]
        
        hero_articles = list(most_viewed) + list(recent_popular)
        # Убираем дубликаты
        seen = set()
        hero_articles = [article for article in hero_articles 
                        if not (article.id in seen or seen.add(article.id))]
        hero_articles = hero_articles[:3]  # Берем максимум 3 уникальные статьи
    
    # Фильтрация по тегу
    tag_slug = request.GET.get('tag')
    if tag_slug:
        articles_list = articles_list.filter(tags__slug=tag_slug)
    
    # Пагинация - 10 статей на страницу
    paginator = Paginator(articles_list, 3)
    page = request.GET.get('page')
    
    try:
        articles = paginator.page(page)
    except PageNotAnInteger:
        # Если page не число, показываем первую страницу
        articles = paginator.page(1)
    except EmptyPage:
        # Если page вне диапазона, показываем последнюю страницу
        articles = paginator.page(paginator.num_pages)
    
    # Получаем общий контекст
    context = get_common_context()
    context.update({
        'articles': articles,
        'categories': Category.objects.all(),
        'current_category': current_category,
        'current_tag': tag_slug,
        'show_hero': show_hero,
        'hero_articles': hero_articles,
    })
    
    return render(request, 'news/article_list.html', context)


def article_detail(request, slug):
    """Детальная страница статьи с комментариями"""
    article = get_object_or_404(Article, slug=slug, is_published=True)
    
    # Увеличиваем счетчик просмотров
    article.increment_views()
    
    # Получаем популярные статьи (исключая текущую)
    popular_articles = Article.objects.filter(
        is_published=True
    ).exclude(id=article.id).order_by('-views')[:5]
    
    # Получаем комментарии к статье (только одобренные и корневые)
    comments = article.comments.filter(is_approved=True, parent__isnull=True)
    
    # Обработка комментариев
    comment_form = CommentForm()
    if request.method == 'POST' and article.comments_enabled:
        return _handle_comment_submission(request, article)
    
    # Определяем какой шаблон использовать
    template_name = 'news/article_detail.html'
    if article.is_game():
        template_name = 'news/game_detail.html'
    
    # Получаем общий контекст
    context = get_common_context()
    context.update({
        'article': article,
        'popular_articles': popular_articles,
        'comments': comments,
        'comment_form': comment_form,
    })
    
    return render(request, template_name, context)

def articles_by_genre(request, genre_slug):
    """Показывает игры по определенному жанру"""
    genre = get_object_or_404(Genre, slug=genre_slug)
    
    # Получаем категорию "Игры"
    games_category = get_object_or_404(Category, slug='igry')
    
    # Фильтруем статьи: только игры с выбранным жанром
    articles = Article.objects.filter(
        category=games_category,
        genres=genre,
        is_published=True
    )
    
    # Получаем общий контекст
    context = get_common_context()
    context.update({
        'articles': articles,
        'genre': genre,
        'current_genre': genre_slug,
    })
    
    return render(request, 'news/articles_by_genre.html', context)


def articles_by_tag(request, tag_slug):
    """Показывает статьи по определенному тегу"""
    tag = get_object_or_404(Tag, slug=tag_slug)
    articles = Article.objects.filter(tags=tag, is_published=True)
    
    # Получаем общий контекст
    context = get_common_context()
    context.update({
        'articles': articles,
        'tag': tag,
    })
    
    return render(request, 'news/articles_by_tag.html', context)


def _handle_comment_submission(request, article):
    """Обработка отправки комментария (вспомогательная функция)"""
    if not request.user.is_authenticated:
        messages.error(request, 'Для добавления комментария необходимо авторизоваться!')
        return redirect('news:article_detail', slug=article.slug)
    
    form = CommentForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Ошибка при добавлении комментария. Проверьте форму.')
        return redirect('news:article_detail', slug=article.slug)
    
    comment = form.save(commit=False)
    comment.article = article
    comment.author = request.user
    
    # Обработка родительского комментария
    parent_id = request.POST.get('parent')
    if parent_id:
        try:
            parent_comment = Comment.objects.get(id=parent_id, article=article)
            comment.parent = parent_comment
        except Comment.DoesNotExist:
            pass
    
    comment.save()
    messages.success(request, 'Ваш комментарий добавлен!')
    return redirect('news:article_detail', slug=article.slug)


@login_required
def add_comment(request, slug):
    """Отдельный обработчик для AJAX добавления комментариев"""
    article = get_object_or_404(Article, slug=slug, is_published=True)
    
    if request.method == 'POST' and article.comments_enabled:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article = article
            comment.author = request.user
            
            # Обработка родительского комментария
            parent_id = request.POST.get('parent')
            if parent_id:
                try:
                    parent_comment = Comment.objects.get(id=parent_id, article=article)
                    comment.parent = parent_comment
                except Comment.DoesNotExist:
                    pass
            
            comment.save()
            
            # Обработка AJAX запроса
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'comment_id': comment.id,
                    'message': 'Комментарий добавлен!'
                })
            else:
                messages.success(request, 'Комментарий добавлен!')
        else:
            # Обработка ошибок AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
            else:
                messages.error(request, 'Ошибка при добавлении комментария!')
    
    return redirect('news:article_detail', slug=article.slug)


@login_required
def delete_comment(request, comment_id):
    """Удаление комментария"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Проверяем права: автор комментария или staff
    if comment.author != request.user and not request.user.is_staff:
        return HttpResponseForbidden("У вас нет прав для удаления этого комментария")
    
    article_slug = comment.article.slug
    
    if request.method == 'POST':
        comment.delete()
        messages.success(request, 'Комментарий удален!')
    else:
        messages.error(request, 'Неверный метод запроса')
    
    return redirect('news:article_detail', slug=article_slug)


def about(request):
    """Страница информации о сайте"""
    context = get_common_context()
    return render(request, 'news/about.html', context)