from django.urls import path, include
from . import views

app_name = 'accounts'

urlpatterns = [
    # 既存のURL
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/setup/', views.profile_setup, name='profile_setup'),
    
    # 設定系URL（追加）
    path('settings/', views.user_settings, name='settings'),
    path('settings/profile/', views.profile_settings, name='profile_settings'),
    path('settings/notifications/', views.notification_settings, name='notification_settings'),
    
    path('logout/', views.logout_view, name='logout'),
    
    # 動画関連のURL
    path('add-video/', views.add_video, name='add_video'),
    path('get-youtube-title/<str:video_id>/', views.get_youtube_title, name='get_youtube_title'),
    
    # その他の機能
    path('ranking/', views.ranking, name='ranking'),
    path('favorites/', views.favorites, name='favorites'),
    path('help/', views.help, name='help'),

    # デバッグ用URL
    path('debug-auth/', views.debug_auth_status, name='debug_auth'),
    path('debug-video/', views.debug_video_status, name='debug_video'),
]