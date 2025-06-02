from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from accounts.utils import get_youtube_service

def home(request):
    """トップページ"""
    return render(request, 'playlist/home.html')

@login_required
def import_video(request):
    """動画インポートページ"""
    return render(request, 'playlist/import_video.html')

@login_required
def get_user_playlists(request):
    """ユーザーのプレイリスト取得（API）"""
    youtube = get_youtube_service(request.user)
    if not youtube:
        return JsonResponse({'error': 'YouTube認証が必要です'})
    
    # YouTube API呼び出し
    try:
        playlists = youtube.playlists().list(
            part='snippet',
            mine=True,
            maxResults=10
        ).execute()
        
        return JsonResponse({'playlists': playlists.get('items', [])})
    except Exception as e:
        return JsonResponse({'error': str(e)})

@login_required
def video_detail(request, video_id):
    """動画詳細ページ"""
    return render(request, 'playlist/video_detail.html', {'video_id': video_id})