from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from .models import UserProfile

class ProfileRequiredMiddleware:
    """プロフィール設定が必要なページでチェックするミドルウェア"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # プロフィール設定が不要なURL
        self.exempt_urls = [
            '/accounts/profile/setup/',
            '/accounts/logout/',
            '/accounts/login/',
            '/accounts/signup/',
            '/admin/',
            '/static/',
            '/media/',
        ]

    def __call__(self, request):
        # ログインユーザーのみチェック
        if request.user.is_authenticated and request.path not in self.exempt_urls:
            # django-allauthのURLもスキップ
            if not any(request.path.startswith(url) for url in self.exempt_urls):
                try:
                    profile = request.user.userprofile
                    if not profile.is_complete():
                        if request.path != '/accounts/profile/setup/':
                            messages.warning(request, 'プロフィール設定を完了してください。')
                            return redirect('accounts:profile_setup')
                except UserProfile.DoesNotExist:
                    if request.path != '/accounts/profile/setup/':
                        messages.info(request, 'プロフィール設定が必要です。')
                        return redirect('accounts:profile_setup')

        response = self.get_response(request)
        return response
