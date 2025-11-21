from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название категории")
    slug = models.SlugField(unique=True, verbose_name="URL")
    
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Genre(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название жанра")
    slug = models.SlugField(unique=True, verbose_name="URL")
    color = models.CharField(max_length=7, default="#A9A9A9", verbose_name="Цвет жанра", 
                           help_text="В формате HEX, например: #805AD5")
    
    class Meta:
        verbose_name = "Жанр"
        verbose_name_plural = "Жанры"
        ordering = ['name']
    
    def __str__(self):
        return self.name

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
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория")
    
    genres = models.ManyToManyField(Genre, blank=True, related_name='articles', verbose_name="Жанры игры")
    game_developer = models.CharField(max_length=200, blank=True, verbose_name="Разработчик игры")
    game_publisher = models.CharField(max_length=200, blank=True, verbose_name="Издатель игры")
    game_release_date = models.DateField(null=True, blank=True, verbose_name="Дата выхода игры")
    game_platforms = models.CharField(max_length=300, blank=True, verbose_name="Платформы (через запятую)")
    game_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Цена игры")
    game_store_link = models.URLField(blank=True, verbose_name="Ссылка на магазин")
    system_requirements = models.TextField(blank=True, verbose_name="Системные требования")
    
    thumbnail = models.ImageField(
        upload_to='articles/thumbnails/%Y/%m/%d/', 
        blank=True, 
        null=True,
        verbose_name="Миниатюра статьи"
    )
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
    
    def is_game(self):
        """Проверяет, является ли статья игрой"""
        return self.category and self.category.slug == 'igry'
    
    def get_platforms_list(self):
        """Возвращает список платформ"""
        if self.game_platforms:
            return [platform.strip() for platform in self.game_platforms.split(',')]
        return []

class ArticleBlock(models.Model):
    BLOCK_TYPES = [
        ('text', 'Текст'),
        ('image', 'Изображение'),
        ('list', 'Список'),          
        ('quote', 'Цитата'),          
        ('warning', 'Предупреждение'), 
        ('info', 'Информация'),       
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