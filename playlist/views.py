from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Playlist, LearningVideo
from accounts.utils import get_youtube_service
import re
import isodate
from django.shortcuts import get_object_or_404
from core.tasks import process_video_async 

@login_required
def add_video(request):
    playlist = Playlist.objects.get(user=request.user)

    if request.method == 'POST':
        video_url = request.POST.get('video_url')
        if not video_url:
            messages.error(request, "動画URLを入力してください。")
            return redirect('playlist:add_video')

        match = re.search(r'(?:v=|youtu\.be/)([\w-]{11})', video_url)
        if not match:
            messages.error(request, "無効なYouTube動画URLです。")
            return redirect('playlist:add_video')

        video_id = match.group(1)

        # 🔽 ここで重複チェック
        if playlist.videos.filter(video_id=video_id).exists():
            messages.info(request, "この動画はすでに再生リストに追加されています。")
            return redirect('playlist:playlist_detail')

        # 動画がDBにない場合はAPIで取得して保存
        video, created = LearningVideo.objects.get_or_create(video_id=video_id)

        if created:
            youtube = get_youtube_service(request.user)
            if not youtube:
                messages.error(request, "YouTube認証が必要です。")
                return redirect('playlist:add_video')
            try:
                response = youtube.videos().list(part="snippet,contentDetails", id=video_id).execute()
                items = response.get('items')
                if not items:
                    messages.error(request, "動画が見つかりません。")
                    return redirect('playlist:add_video')

                item = items[0]
                snippet = item['snippet']
                content_details = item['contentDetails']

                video.title = snippet['title']
                video.description = snippet.get('description', '')
                video.channel_title = snippet.get('channelTitle', '')
                video.thumbnail_url = snippet['thumbnails']['default']['url']
                duration = isodate.parse_duration(content_details['duration'])
                video.duration = int(duration.total_seconds())
                video.save()
            except Exception as e:
                messages.error(request, f"動画情報の取得に失敗しました: {str(e)}")
                return redirect('playlist:add_video')

        # 再生リストに動画を追加
        playlist.videos.add(video)
        # 🔽 クイズ生成の非同期処理を呼び出す（Celery）
        process_video_async.delay(video.id, video_url)


        messages.success(request, "動画を追加しました。")
        return redirect('playlist:playlist_detail')

    return render(request, 'playlist/add_video.html', {'playlist': playlist})


@login_required
def playlist_detail(request):
    playlist = Playlist.objects.get(user=request.user)
    videos = playlist.videos.all()
    return render(request, 'playlist/playlist_detail.html', {'playlist': playlist, 'videos': videos})
