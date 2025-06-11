from allauth.socialaccount.models import SocialToken, SocialAccount
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods  # 追加
from django.views.decorators.csrf import csrf_exempt          # 追加
from django.conf import settings
from .models import UserProfile
import json
import re
import requests

def profile_required(view_func):
    """プロフィール設定が必要な場合にリダイレクトするデコレータ"""
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                profile = request.user.userprofile
                if not profile.is_complete():
                    messages.warning(request, 'プロフィール設定を完了してください。')
                    return redirect('accounts:profile_setup')
            except UserProfile.DoesNotExist:
                messages.info(request, 'プロフィール設定が必要です。')
                return redirect('accounts:profile_setup')
        return view_func(request, *args, **kwargs)
    return wrapper

def get_youtube_service(user):
    """ユーザーのGoogle OAuthトークンを使ってYouTube APIサービスを作成"""
    try:
        # ユーザーのGoogleアカウント情報を取得
        social_account = SocialAccount.objects.get(
            user=user,
            provider='google'
        )
        
        # アクセストークンを取得
        social_token = SocialToken.objects.get(
            account=social_account
        )
        
        # Google Credentialsオブジェクトを作成
        credentials = Credentials(
            token=social_token.token,
            refresh_token=social_token.token_secret,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=None,  # settings.pyから取得される
            client_secret=None,  # settings.pyから取得される
        )
        
        # YouTube APIサービス作成
        youtube = build('youtube', 'v3', credentials=credentials)
        return youtube
        
    except (SocialAccount.DoesNotExist, SocialToken.DoesNotExist):
        return None
    except Exception as e:
        print(f"YouTube service creation error: {e}")
        return None

@login_required
@profile_required
def dashboard(request):
    """学習ダッシュボード（created_at フィールド安全対応）"""
    print(f"🔍 ダッシュボード表示 - ユーザー: {request.user.username}")
    
    try:
        # プレイリストの取得または作成
        from playlist.models import Playlist, LearningVideo
        playlist, created = Playlist.objects.get_or_create(
            user=request.user,
            defaults={'title': 'マイプレイリスト'}
        )
        
        if created:
            print(f"✅ 新規プレイリスト作成: ID={playlist.id}")
        
        print(f"📋 プレイリストID: {playlist.id}, タイトル: {playlist.title}")
        
        # プレイリスト内の動画を取得（created_atフィールドの安全な処理）
        try:
            # まずcreated_atフィールドの存在を確認
            videos = playlist.videos.all().order_by('-created_at', '-id')
            print("✅ created_atフィールドでソート成功")
        except Exception as field_error:
            print(f"⚠️ created_at フィールドエラー、idでソート: {field_error}")
            try:
                videos = playlist.videos.all().order_by('-id')
                print("✅ idフィールドでソート成功")
            except Exception as fallback_error:
                print(f"❌ ソートエラー: {fallback_error}")
                videos = playlist.videos.all()
            
        video_count = videos.count()
        
        print(f"📹 動画数: {video_count}")
        if videos.exists():
            video_titles = [video.title for video in videos[:5]]
            print(f"📹 動画リスト: {video_titles}")
        
        context = {
            'playlist': playlist,
            'videos': videos,
            'video_count': video_count,
            'has_videos': video_count > 0,
            'user_profile': request.user.userprofile,
        }
        
        return render(request, 'accounts/dashboard.html', context)
        
    except Exception as e:
        print(f"❌ ダッシュボードエラー: {e}")
        return render(request, 'accounts/error.html', {'error_message': str(e)})

@login_required
def profile_setup(request):
    """プロフィール設定画面（初回設定・更新）"""
    from .forms import UserProfileForm
    
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'プロフィールを設定しました！')
            
            # 次にアクセスしようとしていたページまたはダッシュボードにリダイレクト
            next_url = request.GET.get('next', 'accounts:dashboard')
            return redirect(next_url)
    else:
        form = UserProfileForm(instance=profile)
    
    context = {
        'form': form,
        'profile': profile,
        'is_first_setup': created or not profile.is_complete(),
    }
    
    return render(request, 'accounts/profile_setup.html', context)

@login_required
def profile_view(request):
    """プロフィール表示（設定済みユーザー向け）"""
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('accounts:profile_setup')
    
    if not profile.is_complete():
        return redirect('accounts:profile_setup')
    
    context = {
        'profile': profile,
        'user': request.user,
    }
    
    return render(request, 'accounts/profile.html', context)

@login_required
def user_settings(request):
    """ユーザー設定画面"""
    return render(request, 'accounts/settings.html')

@login_required
def profile_settings(request):
    """プロフィール設定画面"""
    profile = getattr(request.user, 'userprofile', None)
    
    if request.method == 'POST':
        nickname = request.POST.get('nickname', '').strip()
        birth_date = request.POST.get('birth_date')
        
        if profile:
            if nickname:
                profile.nickname = nickname
            if birth_date:
                profile.birth_date = birth_date
            profile.save()
            
            return JsonResponse({'success': True, 'message': 'プロフィールを更新しました'})
        else:
            return JsonResponse({'success': False, 'error': 'プロフィールが見つかりません'})
    
    context = {
        'profile': profile
    }
    return render(request, 'accounts/profile_settings.html', context)

@login_required
def notification_settings(request):
    """通知設定画面"""
    return render(request, 'accounts/notification_settings.html')

def logout_view(request):
    """ログアウト処理"""
    logout(request)
    messages.success(request, 'ログアウトしました。')
    return redirect('home')

@login_required
def ranking(request):
    """ランキング画面"""
    return render(request, 'accounts/ranking.html')

@login_required
def favorites(request):
    """お気に入り画面"""
    return render(request, 'accounts/favorites.html')

@login_required
def help(request):
    """ヘルプ画面"""
    return render(request, 'accounts/help.html')

# 動画関連機能
@csrf_exempt
@require_http_methods(["POST"])
@login_required
def add_video(request):
    """YouTube動画をプレイリストに追加"""
    try:
        # リクエストデータの取得
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        url = data.get('url', '').strip()
        title = data.get('title', '').strip()
        auto_generate_quiz = data.get('auto_generate_quiz', True)
        
        print(f"🔗 動画追加リクエスト: URL={url[:50]}..., タイトル={title}, 自動クイズ={auto_generate_quiz}")
        
        # URLとタイトルの検証
        if not url or not title:
            return JsonResponse({
                'success': False,
                'error': 'URLとタイトルは必須です'
            })
        
        # YouTube動画IDを抽出
        video_id = extract_youtube_video_id(url)
        if not video_id:
            return JsonResponse({
                'success': False,
                'error': '有効なYouTube URLではありません'
            })
        
        print(f"🎥 抽出された動画ID: {video_id}")
        
        # プレイリストの取得または作成
        from playlist.models import Playlist, LearningVideo
        playlist, created = Playlist.objects.get_or_create(
            user=request.user,
            defaults={'title': 'マイプレイリスト'}
        )
        
        # 既に存在するかチェック
        if LearningVideo.objects.filter(video_id=video_id).exists():
            existing_video = LearningVideo.objects.get(video_id=video_id)
            if existing_video in playlist.videos.all():
                return JsonResponse({
                    'success': False,
                    'error': 'この動画は既にプレイリストに追加されています'
                })
        
        # 動画情報を取得または作成
        video, video_created = LearningVideo.objects.get_or_create(
            video_id=video_id,
            defaults={
                'title': title,
                'description': '',
                'channel_title': '',
                'thumbnail_url': f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg',
                'duration': 0
            }
        )
        
        # プレイリストに追加
        playlist.videos.add(video)
        
        response_data = {
            'success': True,
            'message': '動画を追加しました',
            'video_id': video.id,
            'video_title': video.title,
            'youtube_video_id': video_id
        }
        
        # 自動クイズ生成の実行
        if auto_generate_quiz:
            try:
                print(f"🤖 自動クイズ生成開始: 動画ID {video.id}")
                
                # クイズ生成APIを呼び出し
                from quiz.ai_quiz_generator import AIQuizGenerator
                generator = AIQuizGenerator()
                
                quiz_data = generator.generate_quiz(video.id, request.user)
                
                if quiz_data and quiz_data.get('questions'):
                    from quiz.views import save_ai_quiz_to_database
                    from quiz.views import get_quiz_model
                    
                    Quiz = get_quiz_model()
                    created_count = save_ai_quiz_to_database(quiz_data, video, Quiz)
                    
                    response_data['quiz_generation'] = {
                        'success': True,
                        'quiz_count': created_count,
                        'generation_method': quiz_data.get('generation_method', 'unknown')
                    }
                    print(f"✅ 自動クイズ生成完了: {created_count}問")
                else:
                    response_data['quiz_generation'] = {
                        'success': False,
                        'error': 'クイズ生成に失敗しました'
                    }
                    print("⚠️ 自動クイズ生成失敗")
                    
            except Exception as quiz_error:
                print(f"❌ 自動クイズ生成エラー: {quiz_error}")
                response_data['quiz_generation'] = {
                    'success': False,
                    'error': str(quiz_error)
                }
        
        print(f"✅ 動画追加完了: {video.title}")
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"❌ 動画追加エラー: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_http_methods(["GET"])
@login_required
def get_youtube_title(request, video_id):
    """YouTube動画のタイトルを取得"""
    try:
        print(f"🔍 YouTube タイトル取得: 動画ID {video_id}")
        
        # YouTube Data API v3を使用
        api_key = getattr(settings, 'YOUTUBE_API_KEY', None)
        
        if not api_key:
            # APIキーがない場合のフォールバック
            default_title = f"YouTube動画_{video_id}"
            return JsonResponse({
                'success': True,
                'title': default_title,
                'method': 'fallback',
                'message': 'APIキーが設定されていないため、デフォルトタイトルを返しました'
            })
        
        # YouTube Data API呼び出し
        api_url = f"https://www.googleapis.com/youtube/v3/videos"
        params = {
            'id': video_id,
            'part': 'snippet',
            'key': api_key
        }
        
        response = requests.get(api_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('items') and len(data['items']) > 0:
                video_info = data['items'][0]['snippet']
                title = video_info.get('title', f'YouTube動画_{video_id}')
                
                print(f"✅ タイトル取得成功: {title}")
                
                return JsonResponse({
                    'success': True,
                    'title': title,
                    'method': 'youtube_api',
                    'channel_title': video_info.get('channelTitle', ''),
                    'description': video_info.get('description', '')[:200]  # 最初の200文字
                })
            else:
                # 動画が見つからない場合
                return JsonResponse({
                    'success': False,
                    'error': '動画が見つかりませんでした。プライベート動画または削除された可能性があります。'
                })
        else:
            # API呼び出しエラー
            print(f"❌ YouTube API エラー: {response.status_code}")
            return JsonResponse({
                'success': False,
                'error': f'YouTube APIエラー: {response.status_code}'
            })
            
    except requests.exceptions.Timeout:
        print("⏰ YouTube API タイムアウト")
        return JsonResponse({
            'success': False,
            'error': 'YouTube APIの応答がタイムアウトしました。しばらく後でお試しください。'
        })
    except Exception as e:
        print(f"❌ タイトル取得エラー: {e}")
        return JsonResponse({
            'success': False,
            'error': f'タイトル取得エラー: {str(e)}'
        })

def extract_youtube_video_id(url):
    """YouTube URLから動画IDを抽出"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=)([a-zA-Z0-9_-]{11})',
        r'(?:youtu\.be\/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

# デバッグ用エンドポイント
@login_required
def debug_auth_status(request):
    """認証状況のデバッグ"""
    try:
        profile = request.user.userprofile
        profile_complete = profile.is_complete()
    except UserProfile.DoesNotExist:
        profile = None
        profile_complete = False
    
    debug_info = {
        'user_authenticated': request.user.is_authenticated,
        'username': request.user.username,
        'user_id': request.user.id,
        'has_profile': profile is not None,
        'profile_complete': profile_complete,
        'profile_data': {
            'nickname': getattr(profile, 'nickname', None),
            'birth_date': str(getattr(profile, 'birth_date', None)),
            'age_override': getattr(profile, 'age_override', None),
        } if profile else None
    }
    
    return JsonResponse(debug_info)

@login_required
def debug_video_status(request):
    """動画状況のデバッグ"""
    try:
        from playlist.models import Playlist, LearningVideo
        
        playlist = Playlist.objects.filter(user=request.user).first()
        
        if playlist:
            videos = playlist.videos.all()
            video_data = []
            
            for video in videos:
                video_data.append({
                    'id': video.id,
                    'title': video.title,
                    'video_id': video.video_id,
                    'created_at': video.created_at.isoformat() if hasattr(video, 'created_at') else None
                })
            
            debug_info = {
                'playlist_id': playlist.id,
                'playlist_title': playlist.title,
                'total_videos': len(video_data),
                'playlist_video_count': videos.count(),
                'videos_in_playlist': video_data
            }
        else:
            debug_info = {
                'playlist_id': None,
                'playlist_title': None,
                'total_videos': 0,
                'playlist_video_count': 0,
                'videos_in_playlist': []
            }
        
        return JsonResponse(debug_info)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'debug_info': 'Error occurred during video status debug'
        })

def force_signup_redirect(request):
    """未認証ユーザーをサインアップページにリダイレクト"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    return redirect('account_login')
