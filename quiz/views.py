from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import threading
from playlist.models import LearningVideo  # 動画モデルをインポート
from .models import Quiz, QuizAttempt  # モデルがまだ未定義なのでコメントアウト
# from .tasks import process_video_and_generate_quiz  # まだ未作成なのでコメントアウト
from accounts.utils import get_youtube_service

@login_required
def start_quiz(request, video_id):
    """クイズ開始画面"""
    quizzes = Quiz.objects.filter(video__video_id=video_id)
    if not quizzes.exists():
        return render(request, 'quiz/no_quiz.html', {'video_id': video_id})
    return render(request, 'quiz/start_quiz.html', {
        'quizzes': quizzes,
        'video_id': video_id
    })


@login_required 
def check_process_status(request, video_id):
    """処理状況確認"""
    return JsonResponse({
        'status': 'completed',  # 仮の値
        'message': '処理が完了しました'
    })

@login_required
def submit_answer(request):
    """回答送信"""
    if request.method == 'POST':
        user = request.user
        video_id = request.POST.get('video_id')
        quizzes = Quiz.objects.filter(video__video_id=video_id)

        for quiz in quizzes:
            selected = request.POST.get(f'quiz_{quiz.id}')
            if selected:
                selected = int(selected)
                is_correct = (selected == quiz.correct_option)
                QuizAttempt.objects.create(
                    user=user,
                    quiz=quiz,
                    selected_option=selected,
                    is_correct=is_correct
                )

        return render(request, 'quiz/result.html', {'video_id': video_id})

    return JsonResponse({'error': 'POST method required'})


@login_required
def process_video(request):
    """動画処理（Threading版）"""
    if request.method == 'POST':
        video_url = request.POST.get('video_url')
        
        # 現在は仮実装
        # TODO: 実際の動画処理とクイズ生成を実装
        
        return JsonResponse({
            'status': 'processing',
            'message': '動画を処理中です。しばらくお待ちください。'
        })
        
@login_required
def quiz_list(request, video_id):
    video = get_object_or_404(LearningVideo, id=video_id)
    quizzes = Quiz.objects.filter(video=video)
    return render(request, 'quiz/quiz_list.html', {
        'video': video,
        'quizzes': quizzes
    })
