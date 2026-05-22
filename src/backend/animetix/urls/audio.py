from django.urls import path
from .. import views

urlpatterns = [
    path('clone/', views.clone_voice_api, name='audio_clone'),
    path('lab/', views.audio_lab_view, name='audio_lab'),
]
