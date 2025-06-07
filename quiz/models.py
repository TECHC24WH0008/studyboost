from django.db import models
from django.contrib.auth.models import User
from playlist.models import LearningVideo

class Quiz(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', '初級'),
        ('medium', '中級'),
        ('hard', '上級'),
    ]

    video = models.ForeignKey(LearningVideo, on_delete=models.CASCADE)
    question = models.TextField()
    option_1 = models.CharField(max_length=200)
    option_2 = models.CharField(max_length=200)
    option_3 = models.CharField(max_length=200)
    option_4 = models.CharField(max_length=200)
    correct_option = models.IntegerField(choices=[
        (1, '1'), (2, '2'), (3, '3'), (4, '4')
    ])
    explanation = models.TextField()
    difficulty_level = models.CharField(
        max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Q: {self.question[:30]}... (Video: {self.video_id})"

class QuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    selected_option = models.IntegerField(null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    is_skipped = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'quiz')

    def __str__(self):
        return f"{self.user.username} - Q{self.quiz.id} - {'Correct' if self.is_correct else 'Wrong'}"
