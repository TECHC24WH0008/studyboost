from allauth.socialaccount.models import SocialToken
from googleapiclient.discovery import build
from accounts.utils import get_youtube_service

def get_youtube_service(user):
    """ユーザーのGoogle OAuthトークンを使ってYouTube APIサービスを作成"""
    try:
        social_token = SocialToken.objects.get(
            account__user=user,
            account__provider='google'
        )
        
        youtube = build(
            'youtube', 'v3',
            credentials=social_token.token
        )
        return youtube
        
    except SocialToken.DoesNotExist:
        return None

def check_youtube_permission(user):
    """ユーザーがYouTube APIの権限を持っているかチェック"""
    youtube = get_youtube_service(user)
    return youtube is not None