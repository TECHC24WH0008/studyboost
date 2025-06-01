from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import threading
from .models import Quiz, QuizAttempt
from .tasks import process_video_and_generate_quiz  # 後で作成
from accounts.utils import get_youtube_service

@login_required
def start_quiz(request, video_id):
    """クイズ開始"""
    # クイズデータを取得して表示
    pass

@login_required
def process_video(request):
    """動画処理（Threading版）"""
    if request.method == 'POST':
        video_url = request.POST.get('video_url')
        
        # バックグラウンドで処理開始
        thread = threading.Thread(
            target=process_video_and_generate_quiz,
            args=(video_url, request.user.id)
        )
        thread.start()
        
        return JsonResponse({
            'status': 'processing',
            'message': '動画を処理中です。しばらくお待ちください。'
        })