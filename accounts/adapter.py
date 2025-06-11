# accounts/adapter.py
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect
from django.urls import reverse
from .models import UserProfile
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.shortcuts import get_current_site
from playlist.models import Playlist
import uuid
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        return '/accounts/dashboard/'
    
    def is_open_for_signup(self, request):
        """サインアップページを無効化"""
        return False

class NoSignupRedirectSocialAdapter(DefaultSocialAccountAdapter):
    """ソーシャル認証で追加情報を要求せずに直接ログイン"""
    
    def is_open_for_signup(self, request, sociallogin):
        """サインアップを常に許可"""
        print(f"🔥 is_open_for_signup called - Always return True")
        return True
    
    def new_user(self, request, sociallogin):
        """新しいユーザーを作成"""
        print(f"🔥 new_user called")
        
        # ✅ 新しいUserインスタンスを作成
        user = User()
        
        # Google OAuth からの情報を取得
        extra_data = sociallogin.account.extra_data
        print(f"📋 Extra data: {extra_data}")
        
        # ユーザー情報を設定
        user.email = extra_data.get('email', '')
        user.first_name = extra_data.get('given_name', '')
        user.last_name = extra_data.get('family_name', '')
        
        # ユーザーネームの自動生成
        if user.email:
            base_username = user.email.split('@')[0]
            unique_suffix = uuid.uuid4().hex[:6]
            user.username = f"{base_username}_{unique_suffix}"
        else:
            user.username = f"user_{uuid.uuid4().hex[:8]}"
        
        # パスワードを無効化
        user.set_unusable_password()
        
        print(f"✅ Created new user: {user.username} ({user.email})")
        return user
    
    def save_user(self, request, sociallogin, form=None):
        """ユーザーを保存"""
        print(f"🔥 save_user called - Saving user")
        
        user = sociallogin.user
        
        # ユーザーがまだ保存されていない場合は保存
        if not user.pk:
            user.save()
            print(f"✅ User saved: {user.username}")
        
        # UserProfile作成
        try:
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'nickname': user.get_full_name() or user.username}
            )
            print(f"✅ UserProfile {'created' if created else 'found'}: {profile.nickname}")
        except Exception as e:
            print(f"❌ Error creating UserProfile: {e}")
        
        # 再生リスト作成
        try:
            playlist, created = Playlist.objects.get_or_create(
                user=user,
                defaults={'title': 'マイプレイリスト'}
            )
            print(f"✅ Playlist {'created' if created else 'found'}: {playlist.title}")
        except Exception as e:
            print(f"❌ Error creating Playlist: {e}")
        
        return user
    
    def pre_social_login(self, request, sociallogin):
        """ソーシャルログイン前の処理"""
        print(f"🌀 pre_social_login called")
        
        # メールアドレスで既存ユーザーを検索
        extra_data = sociallogin.account.extra_data
        email = extra_data.get('email')
        
        if email:
            print(f"📧 Looking for existing user with email: {email}")
            try:
                existing_user = User.objects.get(email=email)
                print(f"👤 Found existing user: {existing_user.username}")
                
                # 既存ユーザーを sociallogin に関連付け
                sociallogin.connect(request, existing_user)
                
                # UserProfile確認・作成
                try:
                    profile, created = UserProfile.objects.get_or_create(
                        user=existing_user,
                        defaults={'nickname': existing_user.get_full_name() or existing_user.username}
                    )
                    print(f"✅ UserProfile {'created' if created else 'exists'}")
                except Exception as e:
                    print(f"❌ Error with UserProfile: {e}")
                
                # 再生リスト確認・作成
                try:
                    playlist, created = Playlist.objects.get_or_create(
                        user=existing_user,
                        defaults={'title': 'マイプレイリスト'}
                    )
                    print(f"✅ Playlist {'created' if created else 'exists'}")
                except Exception as e:
                    print(f"❌ Error with Playlist: {e}")
                    
            except User.DoesNotExist:
                print(f"🆕 New user with email: {email}")
        else:
            print("❌ No email found in extra_data")
    
    def get_login_redirect_url(self, request):
        """ログイン後のリダイレクト先"""
        print("🎯 get_login_redirect_url called")
        return '/accounts/dashboard/'
    
    def get_signup_redirect_url(self, request):
        """サインアップ後のリダイレクト先"""
        print("🎯 get_signup_redirect_url called")
        return '/accounts/dashboard/'
    
    def get_connect_redirect_url(self, request, socialaccount):
        """アカウント連携後のリダイレクト先"""
        print("🎯 get_connect_redirect_url called")
        return '/accounts/dashboard/'
    
    def populate_user(self, request, sociallogin, data):
        """ユーザー情報を設定（フォームデータがある場合）"""
        print("🔥 populate_user called")
        user = sociallogin.user
        
        if user:
            # Google OAuth からの情報を取得
            extra_data = sociallogin.account.extra_data
            
            # 既に設定されていない場合のみ設定
            if not user.email:
                user.email = extra_data.get('email', '')
            if not user.first_name:
                user.first_name = extra_data.get('given_name', '')
            if not user.last_name:
                user.last_name = extra_data.get('family_name', '')
            
            print(f"✅ Populated user: {user.username} ({user.email})")
        
        return user