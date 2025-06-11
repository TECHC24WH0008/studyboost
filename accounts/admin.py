from django.contrib import admin
from .models import UserProfile
from allauth.socialaccount.models import SocialToken  # ←追加

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'nickname', 'total_score', 'streak_days', 'created_at']
    list_filter = ['created_at', 'streak_days']
    search_fields = ['user__username', 'nickname']

