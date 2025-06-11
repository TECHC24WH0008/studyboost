from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.shortcuts import redirect

def home_redirect(request):
    """ホーム画面のリダイレクト処理"""
    if request.user.is_authenticated:
        # プロフィール設定チェック
        try:
            profile = request.user.userprofile
            if not profile.is_complete():
                return redirect('accounts:profile_setup')
        except:
            return redirect('accounts:profile_setup')
        
        return redirect('accounts:dashboard')
    else:
        return redirect('account_login')

urlpatterns = [
    # 管理画面
    path('admin/', admin.site.urls),
    
    # ホーム（認証状態に応じてリダイレクト）
    path('', home_redirect, name='home'),
    
    # 認証システム（django-allauth）
    path('accounts/', include('allauth.urls')),
    
    # カスタムアカウント機能（allauthの後に配置）
    path('accounts/', include('accounts.urls')),
    
    # アプリケーション
    path('playlist/', include('playlist.urls')),
    path('quiz/', include('quiz.urls')),
]