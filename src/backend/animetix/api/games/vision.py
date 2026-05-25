from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from dependency_injector.wiring import inject, Provide
from ...containers import Container
from animetix.api.dependencies import get_session_service
from ...models import GameplaySession
from ...forms import VisionQuestForm

# --- VISION QUEST ---

class VisionGameStateView(APIView):
    permission_classes = [permissions.AllowAny]
    
    @inject
    def get(self, request, vision_quest_service = Provide[Container.vision_quest_service]):
        session_service = get_session_service(request)
        port = session_service.port
        state = vision_quest_service.get_state(port)
        if not state.secret_id:
            return Response({"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({
            'media_type': state.media_type,
            'is_daily': state.is_daily,
            'game_over': state.game_over,
            'guesses': state.guesses,
            'best_score': state.best_score,
            'image_url': state.image_url,
            'secret_title': state.secret_title if state.game_over else None
        })

class VisionGameStartView(APIView):
    permission_classes = [permissions.AllowAny]
    
    @inject
    def post(self, request, catalog_service = Provide[Container.catalog_service], vision_quest_service = Provide[Container.vision_quest_service]):
        session_service = get_session_service(request)
        port = session_service.port
        media_type = request.data.get('media_type', port.get('media_type', 'Anime'))
        port.set('media_type', media_type)
        is_daily = request.data.get('is_daily', False)
        
        data = catalog_service.load_data(media_type)
        if not data:
            return Response({"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND)
            
        if is_daily:
            secret_title = port.get('secret_title')
            secret = data['title_to_full_data'].get(secret_title)
        else:
            secret = vision_quest_service.select_secret(data)
            
        if not secret:
            return Response({"error": "Failed to select secret"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        state = vision_quest_service.get_state(port)
        state.secret_id = str(secret['id'])
        state.secret_title = secret['title']
        state.image_url = secret['image']
        state.media_type = media_type
        state.is_daily = is_daily
        state.game_over = False
        state.guesses = []
        state.best_score = 0
        
        vision_quest_service.save_state(port, state)
        
        return Response({
            'media_type': media_type,
            'is_daily': is_daily,
            'game_over': False,
            'guesses': [],
            'best_score': 0,
            'image_url': state.image_url
        })

class VisionGameGuessView(APIView):
    permission_classes = [permissions.AllowAny]
    
    @inject
    def post(self, request, vision_quest_service = Provide[Container.vision_quest_service]):
        session_service = get_session_service(request)
        port = session_service.port
        state = vision_quest_service.get_state(port)
        
        if not state.secret_id:
            return Response({"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST)
        if state.game_over:
            return Response({"error": "Game already over"}, status=status.HTTP_400_BAD_REQUEST)
            
        form = VisionQuestForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            query = form.cleaned_data['description']
            score = vision_quest_service.calculate_score(query, state.secret_id, state.secret_title, state.media_type)
            
            state.guesses.insert(0, {'text': query, 'score': score})
            
            is_new_best = False
            if score > state.best_score:
                state.best_score = score
                is_new_best = True
                
            is_correct = score > 85
            unlocked_achievements = []
            
            if is_correct:
                state.game_over = True
                if request.user.is_authenticated:
                    try:
                        newly_unlocked = request.user.profile.add_win(
                            is_daily=state.is_daily,
                            game_mode='vision',
                            media_type=state.media_type,
                            attempts=len(state.guesses)
                        )
                        if newly_unlocked:
                            for ach in newly_unlocked:
                                unlocked_achievements.append({
                                    'name': ach.name,
                                    'description': ach.description,
                                    'xp_reward': ach.xp_reward,
                                    'badge_url': ach.badge_url if hasattr(ach, 'badge_url') else None
                                })
                    except Exception:
                        pass
                GameplaySession.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    game_mode='vision',
                    media_type=state.media_type,
                    target_item=state.secret_title,
                    history=state.guesses,
                    was_won=True
                )
            
            vision_quest_service.save_state(port, state)
            
            return Response({
                'score': score,
                'is_new_best': is_new_best,
                'best_score': state.best_score,
                'is_correct': is_correct,
                'guesses': state.guesses,
                'game_over': state.game_over,
                'secret_title': state.secret_title if is_correct else None,
                'newly_unlocked_achievements': unlocked_achievements
            })
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
