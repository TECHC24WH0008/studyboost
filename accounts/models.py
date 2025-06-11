from django.db import models
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount
from datetime import date

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=50, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    age_override = models.IntegerField(null=True, blank=True)
    streak_days = models.IntegerField(default=0)
    last_streak_date = models.DateField(null=True, blank=True)
    total_score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_complete(self):
        """プロフィールが完成しているかチェック"""
        return bool(self.nickname and len(self.nickname.strip()) > 0 and self.birth_date)
    
    def get_age(self):
        """現在の年齢を計算"""
        if self.age_override:
            return self.age_override
        
        if not self.birth_date:
            return None
        
        today = date.today()
        age = today.year - self.birth_date.year
        if today.month < self.birth_date.month or (today.month == self.birth_date.month and today.day < self.birth_date.day):
            age -= 1
        return age
    
    def get_age_group(self):
        """年齢グループを取得"""
        age = self.get_age()
        if not age:
            return 'general'
        
        if 6 <= age <= 9:
            return 'elementary_low'
        elif 10 <= age <= 12:
            return 'elementary_mid'
        elif 13 <= age <= 15:
            return 'junior_high'
        elif 16 <= age <= 18:
            return 'high_school'
        else:
            return 'general'
    
    def __str__(self):
        return f"{self.user.username} - {self.nickname or 'No nickname'}"
