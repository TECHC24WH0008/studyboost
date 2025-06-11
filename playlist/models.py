#playlist/models.py
from django.db import models
from django.conf import settings

class Playlist(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    videos = models.ManyToManyField('LearningVideo', related_name='playlists')
    youtube_playlist_id = models.CharField(max_length=255, blank=True, null=True)  # 追加
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f'{self.title} - {self.user.username}'

class LearningVideo(models.Model):
    video_id = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    channel_title = models.CharField(max_length=255, blank=True)
    thumbnail_url = models.URLField(blank=True)
    duration = models.PositiveIntegerField(default=0)  # 秒数
    is_processing = models.BooleanField(default=False)  # 処理中フラグ
    error_message = models.TextField(blank=True, null=True)  # エラーメッセージ
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-created_at']
        verbose_name = '学習動画'
        verbose_name_plural = '学習動画'
    def __str__(self):
        return self.title
