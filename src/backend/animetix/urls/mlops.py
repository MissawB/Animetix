from django.urls import path
from .. import views

urlpatterns = [
    path('feedback/submit/', views.submit_ai_feedback, name='submit_ai_feedback'),
]
