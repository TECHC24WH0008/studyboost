from allauth.socialaccount.models import SocialToken, SocialAccount
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import UserProfile

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

@login_required
def profile_setup(request):
    """初回ログイン後のプロフィール設定"""
    if request.method == 'POST':
        nickname = request.POST.get('nickname')
        birth_date = request.POST.get('birth_date')
        age_override = request.POST.get('age_override')
        
        # UserProfileを作成または更新
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.nickname = nickname
        if birth_date:
            profile.birth_date = birth_date
        if age_override:
            profile.age_override = int(age_override)
        profile.save()
        
        return redirect('/')  # ホームページにリダイレクト
    
    return render(request, 'accounts/profile_setup.html')

@login_required 
def check_youtube_auth(request):
    """YouTube認証状況を確認"""
    youtube = get_youtube_service(request.user)
    if youtube:
        return JsonResponse({'authenticated': True})
    else:
        return JsonResponse({
            'authenticated': False,
            'message': 'Google アカウントでのログインが必要です'
        })