from django.urls import path
from .. import views

urlpatterns = [
    path('transparency/', views.transparency_dashboard, name='transparency'),
    path('webhook/', views.donation_webhook, name='donation_webhook'),
]
