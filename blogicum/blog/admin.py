from django.contrib import admin

from .models import Category, Location, Post, Comment


class PostAdmin(admin.ModelAdmin):
    search_fields = ('text', 'title')
    list_filter = ('pub_date', 'author', 'location', 'category',
                   'is_published', 'created_at')
    list_display = ('pub_date', 'author', 'location', 'category',
                    'is_published', 'created_at', 'title', 'text',)


admin.site.register(Category)
admin.site.register(Location)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment)
