from django.contrib import admin
from .models import Article, ArticleBlock, Tag, Comment, Category, Genre

class ArticleBlockInline(admin.TabularInline):
    model = ArticleBlock
    extra = 1
    fields = ('block_type', 'content', 'image', 'image_caption', 'order')
    ordering = ('order',)

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ('author', 'content', 'is_approved', 'created_at')
    readonly_fields = ('created_at',)
    can_delete = True

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color', 'article_count')
    list_filter = ('name',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    
    def article_count(self, obj):
        return obj.article_set.count()
    article_count.short_description = 'Количество статей'

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color', 'article_count')
    list_filter = ('name',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    
    def article_count(self, obj):
        return obj.articles.count()
    article_count.short_description = 'Количество статей'

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'display_genres', 'created_at', 'views', 'is_published', 'comments_enabled', 'display_tags')
    list_filter = ('is_published', 'created_at', 'author', 'tags', 'comments_enabled', 'category', 'genres')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ArticleBlockInline, CommentInline]
    readonly_fields = ('views',)
    filter_horizontal = ('tags', 'genres')  # Добавляем жанры в filter_horizontal

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['category'].required = True
        return form

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'category', 'thumbnail', 'author', 'is_published')
        }),
        ('Информация об игре (только для категории "Игры")', {
            'fields': ('genres', 'game_developer', 'game_publisher', 'game_release_date', 
                      'game_platforms', 'game_price', 'game_store_link', 'system_requirements'),
            'classes': ('collapse',)
        }),
        ('Комментарии', {
            'fields': ('comments_enabled',)
        }),
        ('Теги', {
            'fields': ('tags',)
        }),
        ('Статистика', {
            'fields': ('views',),
            'classes': ('collapse',)
        }),
    )
    
    def display_tags(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])
    display_tags.short_description = 'Теги'
    
    def display_genres(self, obj):
        return ", ".join([genre.name for genre in obj.genres.all()])
    display_genres.short_description = 'Жанры'

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        # Если статья не является игрой, скрываем блок информации об игре
        if obj and not obj.is_game():
            fieldsets = [fieldset for fieldset in fieldsets if fieldset[0] != 'Информация об игре (только для категории "Игры")']
        return fieldsets

@admin.register(ArticleBlock)
class ArticleBlockAdmin(admin.ModelAdmin):
    list_display = ('article', 'block_type', 'order')
    list_filter = ('block_type', 'article')
    ordering = ('article', 'order')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'article', 'content_preview', 'created_at', 'is_approved', 'parent')
    list_filter = ('is_approved', 'created_at', 'article')
    search_fields = ('content', 'author__username', 'article__title')
    list_editable = ('is_approved',)
    actions = ['approve_comments', 'disapprove_comments']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Текст комментария'
    
    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
    approve_comments.short_description = "Одобрить выбранные комментарии"
    
    def disapprove_comments(self, request, queryset):
        queryset.update(is_approved=False)
    disapprove_comments.short_description = "Снять одобрение с выбранных комментариев"