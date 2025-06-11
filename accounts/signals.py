# accounts/signals.py
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from playlist.models import Playlist
from .models import UserProfile

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile_and_playlist(sender, instance, created, **kwargs):
    if created:
        # UserProfileを作成
        UserProfile.objects.get_or_create(user=instance)
        
        # 再生リストを作成（重複チェック付き）
        Playlist.objects.get_or_create(
            user=instance, 
            defaults={'title': 'マイプレイリスト'}
        )
