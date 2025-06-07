# accounts/signals.py
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from playlist.models import Playlist

User = get_user_model()  # ← これが推奨！

@receiver(post_save, sender=User)
def create_default_playlist(sender, instance, created, **kwargs):
    if created:
        if not Playlist.objects.filter(user=instance).exists():
            Playlist.objects.create(user=instance, title="マイ再生リスト")
