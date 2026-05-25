from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from dependency_injector.wiring import inject, Provide
from ...containers import Container
from animetix.api.dependencies import get_session_service

# --- AKINETIX RL (EXPERT MODE) ---

class AkinetixRLStateView(APIView):
    permission_classes = [permissions.AllowAny]
    
    @inject
    def get(self, request, akinetix_expert_service = Provide[Container.akinetix_expert_service]):
        session_service = get_session_service(request)
        port = session_service.port
        state = akinetix_expert_service.get_state(port)
        if not state.current_q:
            return Response({"error": "No RL session in progress"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(state.model_dump() if hasattr(state, 'model_dump') else state)

class AkinetixRLStartView(APIView):
    permission_classes = [permissions.AllowAny]
    
    @inject
    def post(self, request, catalog_service = Provide[Container.catalog_service], akinetix_expert_service = Provide[Container.akinetix_expert_service]):
        session_service = get_session_service(request)
        port = session_service.port
        media_type = request.data.get('media_type', port.get('media_type', 'Anime'))
        port.set('media_type', media_type)
        
        catalog = catalog_service.load_data(media_type)
        if not catalog:
             return Response({"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND)
        
        state = akinetix_expert_service.start_new_game(catalog['db'])
        akinetix_expert_service.save_state(port, state)
        
        return Response(state.model_dump() if hasattr(state, 'model_dump') else state)

class AkinetixRLAnswerView(APIView):
    permission_classes = [permissions.AllowAny]
    
    @inject
    def post(self, request, catalog_service = Provide[Container.catalog_service], akinetix_expert_service = Provide[Container.akinetix_expert_service]):
        session_service = get_session_service(request)
        port = session_service.port
        state = akinetix_expert_service.get_state(port)
        if not state.current_q:
            return Response({"error": "No RL session in progress"}, status=status.HTTP_400_BAD_REQUEST)
            
        answer = request.data.get('answer')
        media_type = port.get('media_type', 'Anime')
        
        catalog = catalog_service.load_data(media_type)
        if not catalog:
             return Response({"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND)
        
        new_state = akinetix_expert_service.process_answer(catalog['db'], state, answer)
        akinetix_expert_service.save_state(port, new_state)
        
        return Response(new_state.model_dump() if hasattr(new_state, 'model_dump') else new_state)
