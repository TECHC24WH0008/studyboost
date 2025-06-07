from django.urls import path
from . import views

app_name = 'playlist'

urlpatterns = [
    path('', views.playlist_detail, name='playlist_detail'),      # 1つの再生リスト詳細画面
    path('add-video/', views.add_video, name='add_video'),        # 動画追加
]
