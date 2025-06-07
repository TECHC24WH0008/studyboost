from django.db import models
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=50)
    birth_date = models.DateField(null=True, blank=True)
    age_override = models.IntegerField(null=True, blank=True)
    streak_days = models.IntegerField(default=0)
    last_streak_date = models.DateField(null=True, blank=True)
    total_score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_complete(self):
        return bool(self.nickname and self.birth_date) or bool(self.age_override)

    def patched_str(self):
        return str(self.user) + f" ({self.provider})"

    SocialAccount.__str__ = patched_str
