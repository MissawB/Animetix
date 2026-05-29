from django.urls import path
from .. import views

urlpatterns = [
    path('webhook/', views.donation_webhook, name='donation_webhook'),
]
