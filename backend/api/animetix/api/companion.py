from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from dependency_injector.wiring import inject, Provide
from core.domain.services.companion_service import CompanionService
from core.ports.usage_port import UsagePort
from ..containers import Container

class CompanionInteractView(APIView):
    """
    API view for interacting with AI Companions.
    Manages session memory and user quotas.
    """
    permission_classes = [permissions.IsAuthenticated]

    @inject
    def __init__(self, 
                 companion_service: CompanionService = Provide[Container.core.companion_service],
                 usage_port: UsagePort = Provide[Container.infrastructure.usage_port],
                 **kwargs):
        super().__init__(**kwargs)
        self.companion_service = companion_service
        self.usage_port = usage_port

    def post(self, request):
        mentor_id = request.data.get('mentor_id')
        user_message = request.data.get('user_message')
        context_url = request.data.get('context_url', '')

        if not mentor_id or not user_message:
            return Response(
                {"error": "mentor_id and user_message are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check quota
        tier = getattr(request, 'user_tier', 'free')
        if not self.usage_port.check_quota(request.user.id, tier):
            return Response(
                {"error": "AI usage quota exceeded for your tier."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Retrieve history from session
        history = request.session.get('companion_history', [])
        
        try:
            # Generate response
            response_text = self.companion_service.generate_response(
                mentor_id=mentor_id,
                user_msg=user_message,
                context=context_url,
                history=history
            )

            # Update history
            history.append({"role": "user", "content": user_message})
            history.append({"role": "assistant", "content": response_text})
            
            # Keep only last 5 entries
            if len(history) > 5:
                history = history[-5:]
            
            request.session['companion_history'] = history
            
            return Response({
                "response": response_text,
                "history": history
            })
            
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
