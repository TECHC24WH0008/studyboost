from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),  # Google OAuth用
    path('playlist/', include('playlist.urls')),          # トップページ・動画関連
    path('quiz/', include('quiz.urls')),         # クイズ関連
    path('accounts/', include('accounts.urls')),      # API・ユーザー関連
]

# 開発環境でのメディアファイル配信
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)