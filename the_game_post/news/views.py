from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from .models import Article, Tag, Comment
from .forms import CommentForm

def article_list(request):
    articles = Article.objects.filter(is_published=True)
    
    tag_slug = request.GET.get('tag')
    if tag_slug:
        articles = articles.filter(tags__slug=tag_slug)
    
    # Получаем все теги для боковой панели
    all_tags = Tag.objects.all()
    
    return render(request, 'news/article_list.html', {
        'articles': articles,
        'current_tag': tag_slug,
        'all_tags': all_tags
    })

def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug, is_published=True)
    
    # Увеличиваем счетчик просмотров
    article.increment_views()
    
    # Получаем популярные статьи
    popular_articles = Article.objects.filter(
        is_published=True
    ).exclude(
        id=article.id
    ).order_by('-views')[:5]
    
    # Получаем все теги
    all_tags = Tag.objects.all()
    
    # Получаем комментарии к статье
    comments = article.comments.filter(is_approved=True, parent__isnull=True)
    
    # Форма для нового комментария
    comment_form = CommentForm()
    
    if request.method == 'POST' and article.comments_enabled:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            if request.user.is_authenticated:
                comment = comment_form.save(commit=False)
                comment.article = article
                comment.author = request.user
                
                # Проверяем, является ли комментарий ответом
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
            else:
                messages.error(request, 'Для добавления комментария необходимо авторизоваться!')
        else:
            messages.error(request, 'Ошибка при добавлении комментария. Проверьте форму.')
    
    return render(request, 'news/article_detail.html', {
        'article': article,
        'popular_articles': popular_articles,
        'all_tags': all_tags,
        'comments': comments,
        'comment_form': comment_form
    })

def articles_by_tag(request, tag_slug):
    """Показывает статьи по определенному тегу"""
    tag = get_object_or_404(Tag, slug=tag_slug)
    articles = Article.objects.filter(tags=tag, is_published=True)
    
    # Получаем все теги для боковой панели
    all_tags = Tag.objects.all()
    
    return render(request, 'news/articles_by_tag.html', {
        'articles': articles,
        'tag': tag,
        'all_tags': all_tags
    })

@login_required
def add_comment(request, slug):
    article = get_object_or_404(Article, slug=slug, is_published=True)
    
    if request.method == 'POST' and article.comments_enabled:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article = article
            comment.author = request.user
            comment.save()
            messages.success(request, 'Комментарий добавлен!')
        else:
            messages.error(request, 'Ошибка при добавлении комментария!')
    
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
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # AJAX запрос - возвращаем JSON
                return JsonResponse({
                    'success': True,
                    'comment_id': comment.id,
                    'message': 'Комментарий добавлен!'
                })
            else:
                # Обычный запрос - редирект
                messages.success(request, 'Комментарий добавлен!')
        else:
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