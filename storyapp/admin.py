from django.contrib import admin
from .models import User, Theme, Story, StoryResponse

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'created_at')
    search_fields = ('email',)

@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')

@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('character_name', 'theme', 'user', 'created_at', 'email_sent')
    list_filter = ('theme', 'email_sent', 'created_at')
    search_fields = ('character_name', 'user__email')

@admin.register(StoryResponse)
class StoryResponseAdmin(admin.ModelAdmin):
    list_display = ('story', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user_input', 'ai_response')
