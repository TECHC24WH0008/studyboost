from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import re
import requests
from .models import Playlist, LearningVideo

@login_required
def add_video(request):
    try:
        playlist = request.user.playlist
    except Playlist.DoesNotExist:
        playlist = Playlist.objects.create(user=request.user, title='マイプレイリスト')
        
    if request.method == 'POST':
        video_url = request.POST.get('video_url')
        video_title = request.POST.get('video_title')  # ✅ 追加
        
        if not video_url:
            messages.error(request, "動画URLを入力してください。")
            return redirect('accounts:dashboard')
            
        if not video_title:
            messages.error(request, "動画タイトルを入力してください。")
            return redirect('accounts:dashboard')

        match = re.search(r'(?:v=|youtu\.be/)([\w-]{11})', video_url)
        if not match:
            messages.error(request, "無効なYouTube動画URLです。")
            return redirect('accounts:dashboard')

        video_id = match.group(1)

        # 重複チェック
        if playlist.videos.filter(video_id=video_id).exists():
            messages.info(request, "この動画はすでに再生リストに追加されています。")
            return redirect('accounts:dashboard')

        # 動画をデータベースに保存（カスタムタイトル使用）
        video, created = LearningVideo.objects.get_or_create(
            video_id=video_id,
            defaults={'title': video_title}  # ✅ ユーザー入力のタイトルを使用
        )

        if created:
            youtube = get_youtube_service(request.user)
            if youtube:
                try:
                    response = youtube.videos().list(part="snippet,contentDetails", id=video_id).execute()
                    items = response.get('items')
                    if items:
                        item = items[0]
                        snippet = item['snippet']
                        content_details = item['contentDetails']

                        # ユーザーがタイトルを変更していない場合のみ上書き
                        if video.title == video_title and video_title != snippet['title']:
                            video.title = snippet['title']
                        
                        video.description = snippet.get('description', '')
                        video.channel_title = snippet.get('channelTitle', '')
                        video.thumbnail_url = snippet['thumbnails']['default']['url']
                        duration = isodate.parse_duration(content_details['duration'])
                        video.duration = int(duration.total_seconds())
                        video.save()
                except Exception as e:
                    messages.warning(request, f"動画情報の取得に失敗しましたが、追加は完了しました: {str(e)}")

        # 再生リストに動画を追加
        playlist.videos.add(video)
        
        # クイズ生成の非同期処理を呼び出す
        process_video_async.delay(video.id, video_url)

        messages.success(request, f"動画「{video.title}」を追加しました。")
        return redirect('accounts:dashboard')

    return redirect('accounts:dashboard')


@login_required
def playlist_list(request):
    """プレイリスト一覧を表示"""
    try:
        # ユーザーのプレイリストを取得または作成
        playlist, created = Playlist.objects.get_or_create(
            user=request.user,
            defaults={'title': 'マイプレイリスト'}
        )
        
        if created:
            print(f"✅ 新しいプレイリストを作成: {playlist.title}")
        
        # プレイリスト詳細ページにリダイレクト
        return redirect('playlist:playlist_detail', playlist_id=playlist.id)
        
    except Exception as e:
        print(f"❌ プレイリスト一覧エラー: {e}")
        return render(request, 'playlist/error.html', {
            'error_message': str(e)
        })

@login_required
def playlist_detail(request, playlist_id):
    """プレイリスト詳細を表示"""
    try:
        playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
        
        # プレイリスト内の動画を取得
        videos = playlist.videos.all().order_by('-id')
        
        context = {
            'playlist': playlist,
            'videos': videos,
            'video_count': videos.count(),
        }
        
        return render(request, 'playlist/playlist_detail.html', context)
        
    except Exception as e:
        print(f"❌ プレイリスト詳細エラー: {e}")
        return render(request, 'playlist/error.html', {
            'error_message': str(e)
        })

@login_required
def create_playlist(request):
    """新しいプレイリストを作成"""
    if request.method == 'POST':
        title = request.POST.get('title', 'マイプレイリスト')
        
        playlist = Playlist.objects.create(
            user=request.user,
            title=title
        )
        
        return redirect('playlist:playlist_detail', playlist_id=playlist.id)
    
    return render(request, 'playlist/create_playlist.html')

@login_required
@require_http_methods(["GET"])
def get_youtube_title(request, video_id):
    """YouTube動画のタイトルを取得"""
    try:
        print(f"🔍 タイトル取得開始: {video_id}")
        
        # YouTube oEmbed API を使用（APIキー不要）
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        
        response = requests.get(oembed_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            title = data.get('title', f'YouTube動画_{video_id}')
            
            print(f"✅ タイトル取得成功: {title}")
            return JsonResponse({
                'success': True,
                'title': title,
                'video_id': video_id
            })
        else:
            print(f"❌ oEmbed API失敗: {response.status_code}")
            
    except Exception as e:
        print(f"❌ タイトル取得エラー: {e}")
    
    # フォールバック
    return JsonResponse({
        'success': True,
        'title': f'YouTube動画_{video_id}',
        'video_id': video_id
    })

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def add_video_to_playlist(request):
    """プレイリストに動画を追加"""
    try:
        print("➕ 動画追加処理開始")
        
        # JSONデータを解析
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        url = data.get('url', '').strip()
        title = data.get('title', '').strip()
        playlist_id = data.get('playlist_id')
        
        print(f"📊 受信データ: URL={url}, Title={title}, Playlist_ID={playlist_id}")
        
        if not url or not title:
            return JsonResponse({
                'success': False,
                'error': 'URLとタイトルが必要です'
            })
        
        # YouTube URLからビデオIDを抽出
        video_id_match = re.search(r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})', url)
        if not video_id_match:
            return JsonResponse({
                'success': False,
                'error': '有効なYouTube URLではありません'
            })
        
        video_id = video_id_match.group(1)
        print(f"📹 抽出されたVideo ID: {video_id}")
        
        # プレイリストを取得または作成
        if playlist_id:
            try:
                playlist = Playlist.objects.get(id=playlist_id, user=request.user)
            except Playlist.DoesNotExist:
                playlist = Playlist.objects.create(
                    user=request.user,
                    title='マイプレイリスト'
                )
        else:
            playlist, created = Playlist.objects.get_or_create(
                user=request.user,
                defaults={'title': 'マイプレイリスト'}
            )
        
        # LearningVideoを作成または取得
        learning_video, created = LearningVideo.objects.get_or_create(
            video_id=video_id,
            defaults={
                'title': title,
                'is_processing': False
            }
        )
        
        if created:
            print(f"✅ 新しいLearningVideo作成: {learning_video.title}")
        else:
            print(f"📹 既存のLearningVideo取得: {learning_video.title}")
            # タイトルを更新
            learning_video.title = title
            learning_video.save()
        
        # プレイリストに追加（重複チェック）
        if not playlist.videos.filter(id=learning_video.id).exists():
            playlist.videos.add(learning_video)
            print(f"✅ プレイリストに追加: {playlist.title}")
        else:
            print("ℹ️ 動画は既にプレイリストに存在します")
        
        return JsonResponse({
            'success': True,
            'message': '動画を追加しました',
            'video': {
                'id': learning_video.id,
                'title': learning_video.title,
                'video_id': learning_video.video_id,
                'url': f'https://www.youtube.com/watch?v={learning_video.video_id}'
            }
        })
        
    except Exception as e:
        print(f"❌ 動画追加エラー: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
