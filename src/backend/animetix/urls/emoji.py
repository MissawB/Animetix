from django.urls import path
from .. import views

urlpatterns = [
    path('decode/', views.emoji_decode_view, name='emoji_decode'),
    path('guess/', views.emoji_decode_guess, name='emoji_guess'),
]
