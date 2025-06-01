from django.urls import path
from . import views

app_name = 'playlist'

urlpatterns = [
    path('', views.home, name='home'),                                    # トップページ
    path('import/', views.import_video, name='import_video'),             # 動画インポート
    path('playlists/', views.get_user_playlists, name='user_playlists'),  # プレイリスト一覧
    path('video/<str:video_id>/', views.video_detail, name='video_detail'), # 動画詳細
]