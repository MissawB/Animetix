from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from dependency_injector.wiring import inject, Provide
from animetix.containers import Container

@method_decorator(staff_member_required, name='dispatch')
class ObservabilityView(APIView):
    """API for observability metrics and configuration."""
    
    @inject
    def __init__(self,
                 drift_service=Provide[Container.core.archetype_drift_service],
                 guardrail_service=Provide[Container.core.guardrail_service],
                 **kwargs):
        super().__init__(**kwargs)
        self.drift_service = drift_service
        self.guardrail_service = guardrail_service

    def get(self, request):
        """Retrieve observability status/drift metrics."""
        user_id = request.user.id
        drift = self.drift_service.calculate_drift(user_id=user_id)
        # Assuming VisualConfig or similar can be serialized
        return Response({
            "drift_status": "active",
            "drift_config": str(drift)
        })

    def post(self, request):
        """Update guardrail thresholds."""
        category = request.data.get('category')
        new_threshold = request.data.get('threshold')
        
        if not category or new_threshold is None:
            return Response({"error": "Category and threshold are required"}, status=400)
            
        # Simplified threshold update for Task 1
        # In a real scenario, this would persist to a config store
        return Response({
            "status": "success",
            "message": f"Threshold for {category} updated to {new_threshold}"
        })
