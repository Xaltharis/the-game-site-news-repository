from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Article, Tag, Comment, Category
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
    
    return render(request, 'news/register.html', {'form': form})

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
    return render(request, 'news/login.html')


def custom_logout(request):
    """Выход пользователя"""
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы!')
    return redirect('news:article_list')


def get_common_context():
    """Возвращает общий контекст для нескольких представлений"""
    return {
        'all_tags': Tag.objects.all()
    }


def article_list(request, category_slug=None):
    articles_list = Article.objects.filter(is_published=True)
    
    # Фильтрация по категории
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        articles_list = articles_list.filter(category=category)
        current_category = category
    else:
        current_category = None
    
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
    
    all_tags = Tag.objects.all()
    categories = Category.objects.all()
    
    return render(request, 'news/article_list.html', {
        'articles': articles,
        'categories': categories,
        'current_category': current_category,
        'current_tag': tag_slug,
        'all_tags': all_tags
    })


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
    
    context = get_common_context()
    context.update({
        'article': article,
        'popular_articles': popular_articles,
        'comments': comments,
        'comment_form': comment_form,
    })
    
    return render(request, 'news/article_detail.html', context)


def articles_by_tag(request, tag_slug):
    """Показывает статьи по определенному тегу"""
    tag = get_object_or_404(Tag, slug=tag_slug)
    articles = Article.objects.filter(tags=tag, is_published=True)
    
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
    return render(request, 'news/about.html')