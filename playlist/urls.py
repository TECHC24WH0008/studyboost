from django.urls import path
from . import views

app_name = 'playlist'

urlpatterns = [
    # プレイリスト関連
    path('', views.playlist_list, name='playlist_list'),
    path('<int:playlist_id>/', views.playlist_detail, name='playlist_detail'),
    path('create/', views.create_playlist, name='create_playlist'),
    
    # 動画関連のAPI
    path('get-youtube-title/<str:video_id>/', views.get_youtube_title, name='get_youtube_title'),
    path('add-video/', views.add_video_to_playlist, name='add_video'),
]
