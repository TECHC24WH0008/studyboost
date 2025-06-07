# accounts/adapter.py
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.urls import reverse
from .models import UserProfile
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.shortcuts import get_current_site

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        user = request.user

        try:
            profile = user.userprofile
        except UserProfile.DoesNotExist:
            # 初回ログイン → プロフィール作成
            UserProfile.objects.create(user=user)
            return reverse('accounts:profile_setup')

        if not profile.is_complete():
            return reverse('accounts:profile_setup')

        return reverse('accounts:dashboard')  # ログイン後の通常トップページ


class NoSignupRedirectSocialAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        email = sociallogin.account.extra_data.get('email')
        print("✅ is_open_for_signup CALLED")
        print(f"📧 Email: {email}")
        return email is not None

    def pre_social_login(self, request, sociallogin):
        print("🌀 pre_social_login CALLED")

        # 既にユーザーが存在するならスキップ
        if sociallogin.is_existing:
            return

        # Email が一致する既存ユーザーがいれば、それに関連付けてログインさせる
        email = sociallogin.account.extra_data.get('email')
        from django.contrib.auth import get_user_model
        User = get_user_model()

        if email and not sociallogin.is_existing:
            try:
                user = User.objects.get(email=email)
                sociallogin.connect(request, user)
                print("🔗 Connected to existing user")
            except User.DoesNotExist:
                pass  # 通常の flow に進む（save_user が呼ばれる）

    def save_user(self, request, sociallogin, form=None):
        print("🔥 save_user CALLED")

        user = sociallogin.user
        user.set_unusable_password()
        user.email = sociallogin.account.extra_data.get('email', '')
        user.first_name = sociallogin.account.extra_data.get('given_name', '')
        user.last_name = sociallogin.account.extra_data.get('family_name', '')
        user.save()

        return user
    
    def get_app(self, request, provider, **kwargs):
        """
        `get()` ではなく `filter().first()` を使って MultipleObjectsReturned を防止
        """
        current_site = get_current_site(request)
        return SocialApp.objects.filter(provider=provider, sites=current_site).first()