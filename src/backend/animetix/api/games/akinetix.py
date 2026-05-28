from django.utils.decorators import method_decorator
from ratelimit.decorators import ratelimit
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from dependency_injector.wiring import inject, Provide
from ...containers import Container
from animetix.api.dependencies import get_session_service
from ...models import GameplaySession
from animetix_project.logging_config import get_logger

logger = get_logger("animetix." + __name__)

# --- AKINETIX MODE ---

class AkinetixGameStateView(APIView):
    permission_classes = [permissions.AllowAny]
    
    @inject
    def get(self, request, akinetix_service = Provide[Container.akinetix_service]):
        session_service = get_session_service(request)
        port = session_service.port
        state = akinetix_service.get_state(port)
        if not state.current_q:
            return Response({"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({
            'media_type': port.get('media_type', 'Anime'),
            'current_question': state.current_q,
            'history': [q.model_dump() if hasattr(q, 'model_dump') else q for q in state.history],
            'game_over': state.game_over,
            'ai_guess': state.ai_guess,
            'is_daily': state.is_daily
        })

@method_decorator(ratelimit(key='user_or_ip', rate='10/m', method='POST', block=True), name='post')
class AkinetixGameStartView(APIView):
    permission_classes = [permissions.AllowAny]
    
    @inject
    def post(self, request, catalog_service = Provide[Container.catalog_service], akinetix_service = Provide[Container.akinetix_service]):
        session_service = get_session_service(request)
        port = session_service.port
        media_type = request.data.get('media_type', port.get('media_type', 'Anime'))
        if media_type in ['Anime', 'Manga', 'Character']:
            port.set('media_type', media_type)
        is_daily = request.data.get('is_daily', False)
        
        data = catalog_service.load_data(media_type)
        if not data:
            return Response({"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND)
            
        game_state = akinetix_service.start_new_game(data['db'])
        if is_daily:
            game_state.is_daily = True
            
        akinetix_service.save_state(port, game_state)
            
        return Response({
            'status': 'started',
            'media_type': media_type,
            'current_question': game_state.current_q,
            'history': [q.model_dump() if hasattr(q, 'model_dump') else q for q in game_state.history],
            'game_over': game_state.game_over,
            'ai_guess': game_state.ai_guess,
            'is_daily': game_state.is_daily
        })

@method_decorator(ratelimit(key='user_or_ip', rate='10/m', method='POST', block=True), name='post')
class AkinetixGameAnswerView(APIView):
    permission_classes = [permissions.AllowAny]
    
    @inject
    def post(self, request, catalog_service = Provide[Container.catalog_service], akinetix_service = Provide[Container.akinetix_service]):
        session_service = get_session_service(request)
        port = session_service.port
        state = akinetix_service.get_state(port)
        if not state.current_q:
            return Response({"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST)
            
        if state.game_over:
            return Response({"error": "Game already over"}, status=status.HTTP_400_BAD_REQUEST)
            
        answer = request.data.get('answer')
        if not answer:
            return Response({"error": "Answer is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        answer = answer.upper()
        if answer not in ['OUI', 'NON', 'PEUT-ÊTRE', 'PEUT-ETRE']:
            return Response({"error": f"Invalid answer '{answer}'. Expected OUI, NON, or PEUT-ÊTRE."}, status=status.HTTP_400_BAD_REQUEST)
            
        if answer == 'PEUT-ETRE':
            answer = 'PEUT-ÊTRE'
            
        media_type = port.get('media_type', 'Anime')
        data = catalog_service.load_data(media_type)
        if not data:
            return Response({"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND)
            
        new_state = akinetix_service.process_answer(data['db'], state, answer)
        akinetix_service.save_state(port, new_state)
        
        return Response({
            'media_type': media_type,
            'current_question': new_state.current_q,
            'history': [q.model_dump() if hasattr(q, 'model_dump') else q for q in new_state.history],
            'game_over': new_state.game_over,
            'ai_guess': new_state.ai_guess,
            'is_daily': new_state.is_daily
        })

class AkinetixGameConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    
    @inject
    def post(self, request, akinetix_service = Provide[Container.akinetix_service]):
        session_service = get_session_service(request)
        port = session_service.port
        state = akinetix_service.get_state(port)
        
        if not state.current_q and not state.ai_guess:
            return Response({"error": "No game in progress to confirm"}, status=status.HTTP_400_BAD_REQUEST)
            
        correct_val = request.data.get('correct')
        if correct_val is None:
            return Response({"error": "Field 'correct' (boolean) is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        if isinstance(correct_val, str):
            is_correct = correct_val.lower() == 'true'
        else:
            is_correct = bool(correct_val)
            
        media_type = port.get('media_type', 'Anime')
        unlocked_achievements = []
        
        if not is_correct:
            if request.user.is_authenticated:
                try:
                    newly_unlocked = request.user.profile.add_win(
                        is_daily=state.is_daily,
                        game_mode='akinetix',
                        media_type=media_type
                    )
                    if newly_unlocked:
                        for ach in newly_unlocked:
                            unlocked_achievements.append({
                                'name': ach.name,
                                'description': ach.description,
                                'xp_reward': ach.xp_reward,
                                'badge_url': ach.badge_url if hasattr(ach, 'badge_url') else None
                            })
                except Exception as e:
                    logger.error(f"Error updating profile in Akinetix confirm: {e}", exc_info=True)
                    
        GameplaySession.objects.create(
            user=request.user if request.user.is_authenticated else None,
            game_mode='akinetix',
            media_type=media_type,
            target_item=state.ai_guess or "Unknown",
            history=[q.model_dump() if hasattr(q, 'model_dump') else q for q in state.history],
            was_won=is_correct
        )
        
        # Reset the Akinetix session state
        akinetix_service.reset_state(port)
        
        return Response({
            'status': 'confirmed',
            'was_won': is_correct,
            'user_won': not is_correct,
            'newly_unlocked_achievements': unlocked_achievements
        })
