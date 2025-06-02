from django.db import models
from django.contrib.auth.models import User

class LearningVideo(models.Model):
    video_id = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    channel_title = models.CharField(max_length=100)
    thumbnail_url = models.URLField()
    subject = models.CharField(max_length=50, blank=True)
    duration = models.IntegerField()  # 秒数
    transcript = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    is_processed = models.BooleanField(default=False)
    is_learning_video = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Playlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    videos = models.ManyToManyField(LearningVideo, blank=True)
    is_auto_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)