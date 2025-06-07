from django.contrib import admin
from .models import LearningVideo, Playlist

@admin.register(LearningVideo)
class LearningVideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'channel_title']  # 存在するフィールドだけに
    search_fields = ['title', 'channel_title']

@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'created_at', 'updated_at']
