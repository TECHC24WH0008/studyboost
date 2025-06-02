from django.urls import path
from . import views

app_name = 'quiz'

urlpatterns = [
    path('start/<str:video_id>/', views.start_quiz, name='start_quiz'),           # クイズ開始
    path('process-video/', views.process_video, name='process_video'),            # 動画処理
    path('check-status/<str:video_id>/', views.check_process_status, name='check_status'), # 処理状況確認
    path('answer/', views.submit_answer, name='submit_answer'),                   # 回答送信
]