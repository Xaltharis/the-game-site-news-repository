from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название тега")
    slug = models.SlugField(unique=True, verbose_name="URL")
    color = models.CharField(max_length=7, default="#3498db", verbose_name="Цвет тега", 
                           help_text="В формате HEX, например: #3498db")
    
    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Article(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    slug = models.SlugField(unique=True, verbose_name="URL")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    is_published = models.BooleanField(default=True, verbose_name="Опубликовано")
    views = models.PositiveIntegerField(default=0, verbose_name="Просмотры")
    tags = models.ManyToManyField(Tag, blank=True, related_name='articles', verbose_name="Теги")
    comments_enabled = models.BooleanField(default=True, verbose_name="Комментарии включены")
    
    class Meta:
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('news:article_detail', kwargs={'slug': self.slug})
    
    def increment_views(self):
        """Увеличивает счетчик просмотров на 1"""
        self.views += 1
        self.save(update_fields=['views'])
    
    def get_comments_count(self):
        """Возвращает количество комментариев к статье"""
        return self.comments.filter(is_approved=True).count()

class ArticleBlock(models.Model):
    BLOCK_TYPES = [
        ('text', 'Текст'),
        ('image', 'Изображение'),
    ]
    
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='blocks', verbose_name="Статья")
    block_type = models.CharField(max_length=10, choices=BLOCK_TYPES, verbose_name="Тип блока")
    content = models.TextField(blank=True, verbose_name="Содержимое")
    image = models.ImageField(upload_to='articles/%Y/%m/%d/', blank=True, null=True, verbose_name="Изображение")
    image_caption = models.CharField(max_length=300, blank=True, verbose_name="Подпись к изображению")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    
    class Meta:
        verbose_name = "Блок статьи"
        verbose_name_plural = "Блоки статьи"
        ordering = ['order']
    
    def __str__(self):
        return f"{self.article.title} - {self.get_block_type_display()} ({self.order})"

class Comment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments', verbose_name="Статья")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies', verbose_name="Родительский комментарий")
    content = models.TextField(verbose_name="Текст комментария")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    is_approved = models.BooleanField(default=True, verbose_name="Одобрен")
    
    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ['created_at']
    
    def __str__(self):
        return f"Комментарий от {self.author.username} к '{self.article.title}'"
    
    def is_reply(self):
        """Проверяет, является ли комментарий ответом"""
        return self.parent is not None
    
    def get_replies(self):
        """Возвращает все ответы на комментарий"""
        return self.replies.filter(is_approved=True)