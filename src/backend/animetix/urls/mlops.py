from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .. import api_views

router = DefaultRouter()
router.register(r'evaluations', api_views.AIREvaluationViewSet, basename='mlops-eval')
router.register(r'gold-dataset', api_views.GoldDatasetViewSet, basename='mlops-gold')
router.register(r'dpo-curation', api_views.DPOCurationViewSet, basename='mlops-dpo')

urlpatterns = [
    path('', include(router.urls)),
    path('latent-space/', api_views.LatentSpaceAPIView.as_view(), name='mlops-latent-space'),
    path('feedback/submit/', api_views.AIFeedbackAPIView.as_view(), name='submit_ai_feedback'),
]
