from django.contrib import admin 
from .models import Quiz, QuizAttempt

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['question', 'video', 'difficulty_level', 'created_at']
    list_filter = ['difficulty_level', 'created_at']
    search_fields = ['question', 'video__title']

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'quiz', 'is_correct', 'answered_at']
    list_filter = ['is_correct', 'is_skipped', 'answered_at']

