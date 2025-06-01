from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('profile-setup/', views.profile_setup, name='profile_setup'),
    path('check-youtube-auth/', views.check_youtube_auth, name='check_youtube_auth'),
]