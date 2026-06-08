from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from dependency_injector.wiring import inject, Provide
from core.domain.services.companion_service import CompanionService
from core.domain.services.guardrail_service import GuardrailService
from core.ports.usage_port import UsagePort
from ..containers import Container, get_container

class CompanionInteractView(APIView):
    """
    API view for interacting with AI Companions.
    Manages session memory and user quotas.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        container = get_container()
        companion_service = container.core.companion_service()
        guardrail_service = container.core.guardrail_service()
        usage_port = container.infrastructure.usage_port()

        mentor_id = request.data.get('mentor_id')
        user_message = request.data.get('user_message')
        context_url = request.data.get('context_url', '')

        if not mentor_id or not user_message:
            return Response(
                {"error": "mentor_id and user_message are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1. Input Guardrail (Anti-Jailbreak, Moderation)
        guard_input = guardrail_service.validate_input(user_message)
        if not guard_input.get("is_safe", True):
            return Response(
                {"error": guard_input.get("reason", "Inappropriate content detected.")},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check quota
        tier = getattr(request, 'user_tier', 'free')
        if not usage_port.check_quota(request.user.id, tier):
            return Response(
                {"error": "AI usage quota exceeded for your tier."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Retrieve history from session
        history = request.session.get('companion_history', [])
        
        try:
            # Generate response
            response_text = companion_service.generate_response(
                mentor_id=mentor_id,
                user_msg=user_message,
                context=context_url,
                history=history
            )

            # 2. Output Guardrail (Fact-checking, Hallucination)
            guard_output = guardrail_service.validate_output(
                response_text, 
                context=context_url,
                query=user_message
            )
            
            if not guard_output.get("is_safe", True):
                if guard_output.get("action") == "mask":
                    response_text = guard_output.get("warning", response_text)
                else:
                    return Response(
                        {"error": guard_output.get("reason", "Output blocked by security filters.")},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Update history
            history.append({"role": "user", "content": user_message})
            history.append({"role": "assistant", "content": response_text})
            
            # Keep only last 5 entries
            if len(history) > 5:
                history = history[-5:]
            
            request.session['companion_history'] = history

            # Log Usage (Estimating tokens or using units)
            usage_port.log_usage(
                engine=mentor_id, 
                input_tokens=len(user_message) // 4, 
                output_tokens=len(response_text) // 4, 
                user_id=request.user.id
            )
            
            return Response({
                "response": response_text,
                "history": history
            })
            
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
