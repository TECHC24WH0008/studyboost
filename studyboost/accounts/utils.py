from allauth.socialaccount.models import SocialToken, SocialAccount
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def get_youtube_service(user):
    """ユーザーのGoogle OAuthトークンを使ってYouTube APIサービスを作成"""
    try:
        # ユーザーのGoogleアカウント情報を取得
        social_account = SocialAccount.objects.get(
            user=user,
            provider='google'
        )
        
        # アクセストークンを取得
        social_token = SocialToken.objects.get(
            account=social_account
        )
        
        # Google Credentialsオブジェクトを作成
        credentials = Credentials(
            token=social_token.token,
            refresh_token=social_token.token_secret,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=None,  # settings.pyから取得される
            client_secret=None,  # settings.pyから取得される
        )
        
        # YouTube APIサービス作成
        youtube = build('youtube', 'v3', credentials=credentials)
        return youtube
        
    except (SocialAccount.DoesNotExist, SocialToken.DoesNotExist):
        return None
    except Exception as e:
        print(f"YouTube service creation error: {e}")
        return None

def check_youtube_permission(user):
    """ユーザーがYouTube APIの権限を持っているかチェック"""
    youtube = get_youtube_service(user)
    return youtube is not None