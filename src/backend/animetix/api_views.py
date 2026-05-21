from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Profile, DailyChallenge, Achievement, CreativeFusion
from .serializers import ProfileSerializer, DailyChallengeSerializer, AchievementSerializer, MediaItemSerializer, CreativeFusionSerializer
from .containers import get_container
import random

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import CreativeFusion
from .serializers import CreativeFusionSerializer

class ProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint pour visualiser les profils utilisateurs."""
    queryset = Profile.objects.all().select_related('user')
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user.profile)
        return Response(serializer.data)

class CreativeFusionViewSet(viewsets.ModelViewSet):
    """API endpoint pour visualiser, créer, liker et remixer des fusions créatives."""
    queryset = CreativeFusion.objects.all().order_by('-created_at')
    serializer_class = CreativeFusionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        fusion = self.get_object()
        if request.user in fusion.likes.all():
            fusion.likes.remove(request.user)
            return Response({'status': 'unliked', 'likes_count': fusion.likes.count()})
        else:
            fusion.likes.add(request.user)
            return Response({'status': 'liked', 'likes_count': fusion.likes.count()})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def remix(self, request, pk=None):
        parent = self.get_object()
        # Création d'un nouveau fusion basé sur le parent
        remix = CreativeFusion.objects.create(
            title_a=parent.title_a,
            title_b=parent.title_b,
            media_type_a=parent.media_type_a,
            media_type_b=parent.media_type_b,
            chaos_level=request.data.get('chaos_level', parent.chaos_level),
            universe_balance=request.data.get('universe_balance', parent.universe_balance),
            art_style=request.data.get('art_style', parent.art_style),
            creator=request.user,
            parent=parent,
            scenario_text="Remix en cours..."
        )
        serializer = self.get_serializer(remix)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

import base64

import hashlib
import requests
from django.core.cache import cache
from django.http import HttpResponse

def image_proxy_view(request):

    """Proxy pour les images externes avec cache local."""
    encoded_url = request.GET.get('url')
    if not encoded_url: return HttpResponse(status=400)
    
    try:
        url = base64.b64decode(encoded_url).decode('utf-8')
    except:
        return HttpResponse(status=400)

    cache_key = f"img_cache_{hashlib.md5(url.encode()).hexdigest()}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return HttpResponse(cached_data['content'], content_type=cached_data['content_type'])

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            content = response.content
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            cache.set(cache_key, {'content': content, 'content_type': content_type}, 60*60*24*7)
            return HttpResponse(content, content_type=content_type)
    except Exception as e:
        print(f"❌ Image Proxy Error: {e}")
        
    return HttpResponse(status=404)

from .serializers import CreativeFusionSerializer, FriendshipSerializer, SocialUserSerializer

class SocialViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        following = request.user.following.all().select_related('to_user__profile')
        followers = request.user.followers.all().select_related('from_user__profile')
        
        return Response({
            'following': FriendshipSerializer(following, many=True).data,
            'followers': FriendshipSerializer(followers, many=True).data,
        })

    @action(detail=True, methods=['post'])
    def toggle_follow(self, request, pk=None):
        from .models import Friendship
        target_user = User.objects.get(id=pk)
        if target_user == request.user: return Response(status=status.HTTP_400_BAD_REQUEST)
        friendship, created = Friendship.objects.get_or_create(from_user=request.user, to_user=target_user)
        if not created: 
            friendship.delete()
            return Response({'status': 'unfollowed'})
        else: 
            return Response({'status': 'followed'})

class DailyChallengeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DailyChallenge.objects.all()
    serializer_class = DailyChallengeSerializer
    permission_classes = [permissions.AllowAny]

class AchievementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer

class MediaSearchView(APIView):
    """Recherche d'œuvres via SQL (Source of Truth) pour autocomplétion performante."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        media_type = request.query_params.get('media_type')
        query = request.query_params.get('q', '')
        limit = min(int(request.query_params.get('limit', 10)), 50)
        
        if not query and not media_type:
            return Response([])

        # Utilisation de la méthode de recherche SQL centralisée
        results = get_container().catalog_service.search_items(query, media_type, limit)

        
        # Formatage pour le composant d'autocomplétion
        formatted_results = []
        for item in results:
            formatted_results.append({
                'id': item.get('id'),
                'title': item.get('title'),
                'title_english': item.get('title_english'),
                'image': item.get('image'),
                'type': item.get('type')
            })
            
        return Response(formatted_results)

class GameSessionView(APIView):
    """Endpoint pour gérer l'état du jeu via API."""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        # Récupère l'état actuel de la session (compatible avec l'existant)
        return Response({
            "media_type": request.session.get('media_type'),
            "is_ranked": request.session.get('is_ranked'),
            "is_daily": request.session.get('is_daily'),
            "game_over": request.session.get('game_over'),
            "guess_count": len(request.session.get('guesses', []))
        })


from .session_manager import GameSessionManager

class ClassicGameStateView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        session = GameSessionManager(request)
        state = session.get_classic_state()
        media_type = state['media_type']
        secret_title = state['secret_title']
        if not secret_title:
            return Response({"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST)
            
        data = get_container().catalog_service.get_catalog(media_type)
        if not data:
            return Response({"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND)
            
        secret_data = data['title_to_full_data'].get(secret_title)
        if not secret_data:
            return Response({"error": "Secret title data not found"}, status=status.HTTP_404_NOT_FOUND)
            
        from .presenters import GamePresenter
        hints = GamePresenter.format_classic_hints(secret_data, len(state['guesses']), state['revealed_hints'])
        
        return Response({
            'media_type': media_type,
            'difficulty': state['difficulty'],
            'is_daily': state['is_daily'],
            'is_ranked': state['is_ranked'],
            'game_over': state['game_over'],
            'guess_count': len(state['guesses']),
            'guesses': state['guesses'],
            'hints': hints,
            'secret_title': secret_title if state['game_over'] else None,
            'secret_data': secret_data if state['game_over'] else None
        })

class ClassicGameStartView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        session = GameSessionManager(request)
        media_type = request.data.get('media_type', 'Anime')
        difficulty = request.data.get('difficulty', 'Normal')
        override_secret = request.data.get('override_secret')
        
        session.update({'media_type': media_type, 'difficulty': difficulty})
        
        data = get_container().catalog_service.get_catalog(media_type)
        if not data:
            return Response({"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND)
            
        if override_secret:
            secret_title = override_secret
        else:
            session.update({'is_daily': False, 'is_ranked': False})
            from .services import DIFFICULTY_SETTINGS
            secret_title = get_container().game_service.select_secret(media_type, difficulty, DIFFICULTY_SETTINGS)
            
        if not secret_title:
            return Response({"error": "Failed to select secret title"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        session.start_classic_game(secret_title, difficulty, media_type)
        
        return Response({
            'status': 'started',
            'media_type': media_type,
            'difficulty': difficulty,
            'is_daily': False,
            'is_ranked': False,
            'game_over': False,
            'guess_count': 0,
            'guesses': []
        })

class ClassicGameGuessView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        session = GameSessionManager(request)
        state = session.get_classic_state()
        if not state['secret_title']:
            return Response({"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST)
            
        if state['game_over']:
            return Response({"error": "Game already over"}, status=status.HTTP_400_BAD_REQUEST)
            
        guess_title = request.data.get('guess')
        if not guess_title:
            return Response({"error": "Guess is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        media_type = state['media_type']
        secret_title = state['secret_title']
        max_sim = session.get('max_raw_sim', 1.0)
        
        data = get_container().catalog_service.get_catalog(media_type)
        if not data or guess_title not in data['title_to_index']:
            return Response({"error": f"Title '{guess_title}' not in catalog"}, status=status.HTTP_400_BAD_REQUEST)
            
        raw_sim = get_container().game_service.calculate_raw_similarity(media_type, secret_title, guess_title, data)
        secret_item = data['title_to_full_data'].get(secret_title)
        is_correct = get_container().game_service.check_title_match(guess_title, secret_item)
        
        from .presenters import GamePresenter
        score = 100.0 if is_correct else round(min(0.99, (raw_sim / max_sim) * 0.99) * 100, 2)
        color = GamePresenter.get_score_color(score)
        
        g_data = data['title_to_full_data'].get(guess_title, {})
        new_guess = {
            "title": guess_title, 
            "title_english": g_data.get('title_english'), 
            "title_native": g_data.get('title_native'), 
            "image": g_data.get('image'), 
            "score": score, 
            "color": color
        }
        session.add_guess(new_guess)
        
        unlocked_achievements = []
        if is_correct:
            session.set_game_over(True)
            # Handle user profile stats and achievements
            if request.user.is_authenticated:
                item_rank = 100
                for i, item in enumerate(data['lookup']):
                    if (item.get('title') or item.get('name')) == secret_title:
                        item_rank = i + 1; break
                
                try:
                    newly_unlocked = request.user.profile.add_win(
                        is_daily=state['is_daily'], 
                        is_ranked=state['is_ranked'], 
                        item_rank=item_rank, 
                        game_mode='classic', 
                        media_type=media_type, 
                        attempts=len(state['guesses']) + 1
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
                
            from .models import GameplaySession
            GameplaySession.objects.create(
                user=request.user if request.user.is_authenticated else None, 
                game_mode='classic', 
                media_type=media_type, 
                target_item=secret_title, 
                history=session.get('guesses'), 
                was_won=True
            )
            
        # Get updated state
        updated_state = session.get_classic_state()
        hints = GamePresenter.format_classic_hints(secret_item, len(updated_state['guesses']), updated_state['revealed_hints'])
        
        return Response({
            'media_type': media_type,
            'game_over': updated_state['game_over'],
            'guess_count': len(updated_state['guesses']),
            'guesses': updated_state['guesses'],
            'latest_guess': new_guess,
            'is_correct': is_correct,
            'hints': hints,
            'secret_title': secret_title if updated_state['game_over'] else None,
            'secret_data': secret_item if updated_state['game_over'] else None,
            'newly_unlocked_achievements': unlocked_achievements
        })

class ClassicGameRevealView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        session = GameSessionManager(request)
        state = session.get_classic_state()
        if not state['secret_title']:
            return Response({"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST)
            
        hint_type = request.data.get('hint_type')
        if not hint_type:
            return Response({"error": "Hint type is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        session.reveal_hint(hint_type)
        
        # Get updated hints
        media_type = state['media_type']
        secret_title = state['secret_title']
        data = get_container().catalog_service.get_catalog(media_type)
        secret_data = data['title_to_full_data'].get(secret_title)
        
        from .presenters import GamePresenter
        updated_state = session.get_classic_state()
        hints = GamePresenter.format_classic_hints(secret_data, len(updated_state['guesses']), updated_state['revealed_hints'])
        
        return Response({
            'revealed_hints': updated_state['revealed_hints'],
            'hints': hints
        })

class AkinetixGameStateView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        session = GameSessionManager(request)
        state = session.get_akinetix_state()
        if not state.get('current_q'):
            return Response({"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({
            'media_type': session.get_current_mode(),
            'current_question': state['current_q'],
            'history': state['history'],
            'game_over': state['game_over'],
            'ai_guess': state['ai_guess'],
            'is_daily': state['is_daily']
        })

class AkinetixGameStartView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        session = GameSessionManager(request)
        media_type = request.data.get('media_type', session.get_current_mode())
        session.switch_mode(media_type)
        is_daily = request.data.get('is_daily', False)
        
        data = get_container().catalog_service.load_data(media_type)
        if not data:
            return Response({"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND)
            
        game_state = get_container().akinetix_service.start_new_game(data['db'])
        session.start_akinetix_game(game_state)
        if is_daily:
            session.set('is_daily', True)
            
        updated_state = session.get_akinetix_state()
        return Response({
            'status': 'started',
            'media_type': media_type,
            'current_question': updated_state['current_q'],
            'history': updated_state['history'],
            'game_over': updated_state['game_over'],
            'ai_guess': updated_state['ai_guess'],
            'is_daily': updated_state['is_daily']
        })

class AkinetixGameAnswerView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        session = GameSessionManager(request)
        state = session.get_akinetix_state()
        if not state.get('current_q'):
            return Response({"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST)
            
        if state.get('game_over'):
            return Response({"error": "Game already over"}, status=status.HTTP_400_BAD_REQUEST)
            
        answer = request.data.get('answer')
        if not answer:
            return Response({"error": "Answer is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        answer = answer.upper()
        if answer not in ['OUI', 'NON', 'PEUT-ÊTRE', 'PEUT-ETRE']:
            return Response({"error": f"Invalid answer '{answer}'. Expected OUI, NON, or PEUT-ÊTRE."}, status=status.HTTP_400_BAD_REQUEST)
            
        if answer == 'PEUT-ETRE':
            answer = 'PEUT-ÊTRE'
            
        media_type = session.get_current_mode()
        data = get_container().catalog_service.load_data(media_type)
        if not data:
            return Response({"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND)
            
        new_state = get_container().akinetix_service.process_answer(data['db'], state, answer)
        session.update_akinetix_state(new_state)
        
        updated_state = session.get_akinetix_state()
        return Response({
            'media_type': media_type,
            'current_question': updated_state['current_q'],
            'history': updated_state['history'],
            'game_over': updated_state['game_over'],
            'ai_guess': updated_state['ai_guess'],
            'is_daily': updated_state['is_daily']
        })

class AkinetixGameConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        session = GameSessionManager(request)
        state = session.get_akinetix_state()
        if not state.get('current_q') and not state.get('ai_guess'):
            return Response({"error": "No game in progress to confirm"}, status=status.HTTP_400_BAD_REQUEST)
            
        correct_val = request.data.get('correct')
        if correct_val is None:
            return Response({"error": "Field 'correct' (boolean) is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        if isinstance(correct_val, str):
            is_correct = correct_val.lower() == 'true'
        else:
            is_correct = bool(correct_val)
            
        media_type = session.get_current_mode()
        unlocked_achievements = []
        
        if not is_correct:
            if request.user.is_authenticated:
                try:
                    newly_unlocked = request.user.profile.add_win(
                        is_daily=state.get('is_daily', False),
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
                except Exception:
                    pass
                    
        from .models import GameplaySession
        GameplaySession.objects.create(
            user=request.user if request.user.is_authenticated else None,
            game_mode='akinetix',
            media_type=media_type,
            target_item=state.get('ai_guess') or "Unknown",
            history=state.get('history', []),
            was_won=is_correct
        )
        
        # Reset the Akinetix session state
        session.update({
            'akinetix_probs': None,
            'akinetix_asked_attrs': None,
            'akinetix_current_q': None,
            'akinetix_history': None,
            'akinetix_ai_guess': None,
            'akinetix_game_over': False
        })
        
        return Response({
            'status': 'confirmed',
            'was_won': is_correct,
            'user_won': not is_correct,
            'newly_unlocked_achievements': unlocked_achievements
        })

class EmojiGameStateView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        session = GameSessionManager(request)
        state = session.get_emoji_state()
        if not state.get('secret'):
            return Response({"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({
            'media_type': session.get_current_mode(),
            'emojis': state['emojis'],
            'guesses': state['guesses'],
            'game_over': state['game_over'],
            'is_daily': state['is_daily'],
            'is_ranked': state['is_ranked'],
            'secret_title': state['secret'] if state['game_over'] else None
        })

class EmojiGameStartView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        session = GameSessionManager(request)
        media_type = request.data.get('media_type', session.get_current_mode())
        session.switch_mode(media_type)
        is_daily = request.data.get('is_daily', False)
        is_ranked = request.data.get('is_ranked', False)
        
        data = get_container().catalog_service.load_data(media_type)
        if not data:
            return Response({"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND)
            
        if is_daily or is_ranked:
            secret = session.get('secret_title')
        else:
            secret = get_container().emoji_service.select_secret(data)
            
        if not secret:
            return Response({"error": "Failed to select secret title"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        secret_data = data['title_to_full_data'].get(secret, {})
        description = secret_data.get('description', '')
        
        emoji_list = get_container().emoji_service.generate_emojis(media_type, secret, description)
        session.start_emoji_game(secret, emoji_list)
        if is_daily:
            session.set('is_daily', True)
        if is_ranked:
            session.set('is_ranked', True)
            
        updated_state = session.get_emoji_state()
        return Response({
            'status': 'started',
            'media_type': media_type,
            'emojis': updated_state['emojis'],
            'guesses': updated_state['guesses'],
            'game_over': updated_state['game_over'],
            'is_daily': updated_state['is_daily'],
            'is_ranked': updated_state['is_ranked']
        })

class EmojiGameGuessView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        session = GameSessionManager(request)
        state = session.get_emoji_state()
        if not state.get('secret'):
            return Response({"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST)
            
        if state.get('game_over'):
            return Response({"error": "Game already over"}, status=status.HTTP_400_BAD_REQUEST)
            
        guess_title = request.data.get('guess')
        if not guess_title:
            return Response({"error": "Guess is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        media_type = session.get_current_mode()
        data = get_container().catalog_service.load_data(media_type)
        if not data or guess_title not in data.get('title_to_index', {}):
            return Response({"error": f"Title '{guess_title}' not in catalog"}, status=status.HTTP_400_BAD_REQUEST)
            
        secret = state['secret']
        guess_full = data['title_to_full_data'].get(guess_title)
        secret_item = data['title_to_full_data'].get(secret)
        
        is_correct = get_container().game_service.check_title_match(guess_title, secret_item)
        
        guesses = state['guesses']
        new_guess = {
            'title': guess_title,
            'title_en': guess_full.get('title_english'),
            'title_jp': guess_full.get('title_native'),
            'image': guess_full.get('image'),
            'is_correct': is_correct
        }
        guesses.append(new_guess)
        session.set('emoji_guesses', guesses)
        
        unlocked_achievements = []
        if is_correct:
            session.set('emoji_game_over', True)
            if request.user.is_authenticated:
                item_rank = 100
                for i, item in enumerate(data['lookup']):
                    if (item.get('title') or item.get('name')) == secret:
                        item_rank = i + 1
                        break
                try:
                    newly_unlocked = request.user.profile.add_win(
                        is_daily=state['is_daily'],
                        is_ranked=state['is_ranked'],
                        item_rank=item_rank,
                        game_mode='emoji',
                        media_type=media_type,
                        attempts=len(guesses)
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
                    
            from .models import GameplaySession
            GameplaySession.objects.create(
                user=request.user if request.user.is_authenticated else None,
                game_mode='emoji',
                media_type=media_type,
                target_item=secret,
                history=guesses,
                was_won=True
            )
            
        updated_state = session.get_emoji_state()
        return Response({
            'media_type': media_type,
            'game_over': updated_state['game_over'],
            'guess_count': len(updated_state['guesses']),
            'guesses': updated_state['guesses'],
            'latest_guess': new_guess,
            'is_correct': is_correct,
            'secret_title': secret if updated_state['game_over'] else None,
            'newly_unlocked_achievements': unlocked_achievements
        })

class ParadoxGameStateView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        session = GameSessionManager(request)
        state = session.get_paradox_state()
        if not state.get('answer'):
            return Response({"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST)
            
        media_type = state['media']
        data = get_container().catalog_service.load_data(media_type)
        
        options = []
        for t in state['options']:
            options.append({
                'title': t,
                'image': data['title_to_full_data'].get(t, {}).get('image') if data else None
            })
            
        return Response({
            'media_type': media_type,
            'scenario': state['scenario'],
            'options': options,
            'game_over': session.get('paradox_game_over', False),
            'is_daily': state['is_daily']
        })

class ParadoxGameStartView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        session = GameSessionManager(request)
        media_type = request.data.get('media_type', session.get_current_mode())
        session.switch_mode(media_type)
        is_daily = request.data.get('is_daily', False)
        
        data = get_container().catalog_service.load_data(media_type)
        if not data:
            return Response({"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND)
            
        secret_title = session.get('secret_title')
        res_prepare = get_container().paradox_service.prepare_challenge(data, is_daily, secret_title)
        if not res_prepare or len(res_prepare) < 3:
            return Response({"error": "Failed to prepare paradox challenge"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        t1, t2, intruder = res_prepare
        language = session.get('language', 'Français')
        
        res = get_container().paradox_service.generate_logic(
            media_type,
            data['title_to_full_data'][t1],
            data['title_to_full_data'][t2],
            data['title_to_full_data'][intruder],
            language
        )
        
        session.start_paradox_game(intruder, [t1, t2, intruder], res.reasoning, res.scenario, media_type)
        if is_daily:
            session.set('is_daily', True)
        session.set('paradox_game_over', False)
            
        updated_state = session.get_paradox_state()
        options = []
        for t in updated_state['options']:
            options.append({
                'title': t,
                'image': data['title_to_full_data'].get(t, {}).get('image') if data else None
            })
            
        return Response({
            'status': 'started',
            'media_type': media_type,
            'scenario': updated_state['scenario'],
            'options': options,
            'game_over': False,
            'is_daily': updated_state['is_daily']
        })

class ParadoxGameGuessView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        session = GameSessionManager(request)
        state = session.get_paradox_state()
        if not state.get('answer'):
            return Response({"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST)
            
        if session.get('paradox_game_over', False):
            return Response({"error": "Game already over"}, status=status.HTTP_400_BAD_REQUEST)
            
        guess_title = request.data.get('guess')
        if not guess_title:
            return Response({"error": "Guess is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        choice = guess_title
        answer = state['answer']
        is_correct = (choice == answer)
        
        session.set('paradox_game_over', True)
        
        media_type = state['media']
        data = get_container().catalog_service.load_data(media_type)
        
        unlocked_achievements = []
        if is_correct:
            if request.user.is_authenticated:
                try:
                    newly_unlocked = request.user.profile.add_win(
                        is_daily=state['is_daily'],
                        game_mode='paradox',
                        media_type=media_type,
                        attempts=1
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
                    
            from .models import GameplaySession
            GameplaySession.objects.create(
                user=request.user if request.user.is_authenticated else None,
                game_mode='paradox',
                media_type=media_type,
                target_item=answer,
                history=[{'guess': choice, 'is_correct': is_correct}],
                was_won=is_correct
            )
            
        final_opts = []
        for t in state['options']:
            final_opts.append({
                'title': t,
                'is_intruder': (t == answer),
                'is_user_choice': (t == choice),
                'image': data['title_to_full_data'].get(t, {}).get('image') if data else None
            })
            
        return Response({
            'media_type': media_type,
            'is_correct': is_correct,
            'answer': answer,
            'reasoning': state['reasoning'],
            'final_options': final_opts,
            'newly_unlocked_achievements': unlocked_achievements
        })

# --- VISION QUEST REST API ---

class VisionGameStateView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        session = GameSessionManager(request)
        state = session.get_vision_state()
        if not state.get('secret_id'):
            return Response({"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({
            'media_type': state.get('media_type', 'Anime'),
            'is_daily': state.get('is_daily', False),
            'game_over': state.get('game_over', False),
            'guesses': state.get('guesses', []),
            'best_score': state.get('best_score', 0),
            'image_url': state.get('image_url'),
            'secret_title': state.get('secret_title') if state.get('game_over') else None
        })

class VisionGameStartView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        session = GameSessionManager(request)
        media_type = request.data.get('media_type', session.get_current_mode())
        is_daily = request.data.get('is_daily', False)
        
        data = get_container().catalog_service.load_data(media_type)
        if not data:
            return Response({"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND)
            
        if is_daily:
            secret_title = session.get('secret_title')
            secret = data['title_to_full_data'].get(secret_title)
        else:
            secret = get_container().vision_quest_service.select_secret(data)
            
        if not secret:
            return Response({"error": "Failed to select secret"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        session.start_vision_game(str(secret['id']), secret['title'], secret['image'], media_type)
        if is_daily:
            session.set('is_daily', True)
            
        state = session.get_vision_state()
        return Response({
            'media_type': media_type,
            'is_daily': is_daily,
            'game_over': False,
            'guesses': [],
            'best_score': 0,
            'image_url': state.get('image_url')
        })

from .forms import VisionQuestForm
class VisionGameGuessView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        session = GameSessionManager(request)
        state = session.get_vision_state()
        
        if not state.get('secret_id'):
            return Response({"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST)
        if state.get('game_over'):
            return Response({"error": "Game already over"}, status=status.HTTP_400_BAD_REQUEST)
            
        form = VisionQuestForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            query = form.cleaned_data['description']
            secret_id = state['secret_id']
            secret_title = state['secret_title']
            media_type = state['media_type']
            is_daily = state['is_daily']
            
            score = get_container().vision_quest_service.calculate_score(query, secret_id, secret_title, media_type)
            
            guesses = state['guesses']
            guesses.insert(0, {'text': query, 'score': score})
            session.set('vision_guesses', guesses)
            
            best_score = state['best_score']
            is_new_best = False
            if score > best_score:
                best_score = score
                is_new_best = True
                session.set('vision_best_score', best_score)
                
            is_correct = score > 85 # 85 is the threshold used in old views
            unlocked_achievements = []
            
            if is_correct:
                session.set('vision_game_over', True)
                if request.user.is_authenticated:
                    try:
                        newly_unlocked = request.user.profile.add_win(
                            is_daily=is_daily,
                            game_mode='vision',
                            media_type=media_type,
                            attempts=len(guesses)
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
                from .models import GameplaySession
                GameplaySession.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    game_mode='vision',
                    media_type=media_type,
                    target_item=secret_title,
                    history=guesses,
                    was_won=True
                )
            
            return Response({
                'score': score,
                'is_new_best': is_new_best,
                'best_score': best_score,
                'is_correct': is_correct,
                'guesses': guesses,
                'game_over': is_correct,
                'secret_title': secret_title if is_correct else None,
                'newly_unlocked_achievements': unlocked_achievements
            })
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- BLINDTEST REST API ---

class BlindtestGameStateView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        session = GameSessionManager(request)
        state = session.get_blindtest_state()
        if not state.get('secret'):
            return Response({"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({
            'video_url': state.get('video'),
            'theme_type': state.get('type'),
            'blindtest_song': state.get('song'),
            'blindtest_artists': state.get('artists'),
            'guesses': state.get('guesses', []),
            'game_over': state.get('game_over', False),
            'is_daily': state.get('is_daily', False),
            'secret_title': state.get('secret') if state.get('game_over') else None
        })

class BlindtestGameStartView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        session = GameSessionManager(request)
        media_type = "Anime"
        is_daily = request.data.get('is_daily', False)
        theme_pref = request.data.get('type')
        
        data = get_container().catalog_service.load_data(media_type)
        if not data:
            return Response({"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND)
            
        import datetime
        if is_daily:
            theme = get_container().blindtest_service.get_daily_theme(datetime.date.today())
        else:
            theme = get_container().blindtest_service.get_random_theme(theme_type=theme_pref)
            
        if not theme:
            return Response({"error": "Failed to select theme"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        session.start_blindtest_game(theme)
        if is_daily:
            session.set('is_daily', True)
            
        state = session.get_blindtest_state()
        return Response({
            'video_url': state.get('video'),
            'theme_type': state.get('type'),
            'blindtest_song': state.get('song'),
            'blindtest_artists': state.get('artists'),
            'guesses': [],
            'game_over': False,
            'is_daily': is_daily
        })

class BlindtestGameGuessView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        session = GameSessionManager(request)
        state = session.get_blindtest_state()
        
        if not state.get('secret'):
            return Response({"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST)
        if state.get('game_over'):
            return Response({"error": "Game already over"}, status=status.HTTP_400_BAD_REQUEST)
            
        guess_title = request.data.get('guess')
        if not guess_title:
            return Response({"error": "Guess is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        media_type = "Anime"
        data = get_container().catalog_service.load_data(media_type)
        is_daily = state.get('is_daily', False)
        secret = state['secret']
        
        secret_item = data['title_to_full_data'].get(secret)
        is_correct = get_container().game_service.check_title_match(guess_title, secret_item)
        
        guesses = state['guesses']
        guess_full = data['title_to_full_data'].get(guess_title, {})
        
        image_url = None
        if guess_full and guess_full.get('image'):
            image_url = str(guess_full.get('image'))
            
        guesses.append({
            'title': str(guess_title),
            'image': image_url,
            'is_correct': bool(is_correct)
        })
        session.set('blindtest_guesses', guesses)
        
        unlocked_achievements = []
        if is_correct:
            session.set('blindtest_game_over', True)
            if request.user.is_authenticated:
                try:
                    newly_unlocked = request.user.profile.add_win(
                        is_daily=is_daily,
                        game_mode='blindtest',
                        media_type=media_type,
                        attempts=len(guesses)
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
            from .models import GameplaySession
            GameplaySession.objects.create(
                user=request.user if request.user.is_authenticated else None,
                game_mode='blindtest',
                media_type=media_type,
                target_item=secret,
                history=guesses,
                was_won=True
            )
            
        return Response({
            'is_correct': is_correct,
            'guesses': guesses,
            'game_over': is_correct,
            'secret_title': secret if is_correct else None,
            'newly_unlocked_achievements': unlocked_achievements
        })

# --- COVERTEST REST API ---

class CovertestGameStateView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        session = GameSessionManager(request)
        state = session.get_covertest_state()
        if not state.get('secret'):
            return Response({"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({
            'cover_url': state.get('url'),
            'locale': state.get('locale'),
            'volume': state.get('volume'),
            'guesses': state.get('guesses', []),
            'game_over': state.get('game_over', False),
            'is_daily': state.get('is_daily', False),
            'secret_title': state.get('secret') if state.get('game_over') else None
        })

class CovertestGameStartView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        session = GameSessionManager(request)
        media_type = "Manga"
        is_daily = request.data.get('is_daily', False)
        
        data = get_container().catalog_service.load_data(media_type)
        if not data:
            return Response({"error": "Catalog not found"}, status=status.HTTP_404_NOT_FOUND)
            
        import datetime
        if is_daily:
            cover = get_container().covertest_service.get_daily_cover(datetime.date.today())
        else:
            cover = get_container().covertest_service.get_random_cover()
            
        if not cover:
            return Response({"error": "Failed to select cover"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        session.start_covertest_game(cover)
        if is_daily:
            session.set('is_daily', True)
            
        state = session.get_covertest_state()
        return Response({
            'cover_url': state.get('url'),
            'locale': state.get('locale'),
            'volume': state.get('volume'),
            'guesses': [],
            'game_over': False,
            'is_daily': is_daily
        })

class CovertestGameGuessView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        session = GameSessionManager(request)
        state = session.get_covertest_state()
        
        if not state.get('secret'):
            return Response({"error": "No game in progress"}, status=status.HTTP_400_BAD_REQUEST)
        if state.get('game_over'):
            return Response({"error": "Game already over"}, status=status.HTTP_400_BAD_REQUEST)
            
        guess_title = request.data.get('guess')
        if not guess_title:
            return Response({"error": "Guess is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        media_type = "Manga"
        data = get_container().catalog_service.load_data(media_type)
        is_daily = state.get('is_daily', False)
        secret = state['secret']
        
        secret_item = data['title_to_full_data'].get(secret)
        is_correct = get_container().game_service.check_title_match(guess_title, secret_item)
        
        guesses = state['guesses']
        guess_full = data['title_to_full_data'].get(guess_title, {})
        
        image_url = None
        if guess_full and guess_full.get('image'):
            image_url = str(guess_full.get('image'))
            
        guesses.append({
            'title': str(guess_title),
            'image': image_url,
            'is_correct': bool(is_correct)
        })
        session.set('covertest_guesses', guesses)
        
        unlocked_achievements = []
        if is_correct:
            session.set('covertest_game_over', True)
            if request.user.is_authenticated:
                try:
                    newly_unlocked = request.user.profile.add_win(
                        is_daily=is_daily,
                        game_mode='covertest',
                        media_type=media_type,
                        attempts=len(guesses)
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
            from .models import GameplaySession
            GameplaySession.objects.create(
                user=request.user if request.user.is_authenticated else None,
                game_mode='covertest',
                media_type=media_type,
                target_item=secret,
                history=guesses,
                was_won=True
            )
            
        return Response({
            'is_correct': is_correct,
            'guesses': guesses,
            'game_over': is_correct,
            'secret_title': secret if is_correct else None,
            'newly_unlocked_achievements': unlocked_achievements
        })

# --- ARCHETYPIST REST API ---

from .models import CreativeFusion
from celery.result import AsyncResult

class ArchetypistStartFusionView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        session = GameSessionManager(request)
        media_type = session.get_current_mode()
        
        title_A = request.data.get('title_A')
        title_B = request.data.get('title_B')
        media_A = request.data.get('media_type_A', media_type)
        media_B = request.data.get('media_type_B', media_type)
        
        chaos_level = int(request.data.get('chaos_level', 50))
        universe_balance = int(request.data.get('universe_balance', 50))
        art_style = request.data.get('art_style', 'Cyberpunk')
        parent_id = request.data.get('parent_id')
        
        data = get_container().catalog_service.load_data(media_type)
        data_A = get_container().catalog_service.load_data(media_A) if media_A != media_type else data
        data_B = get_container().catalog_service.load_data(media_B) if media_B != media_type else data
        
        if not data_A or not data_B:
            return Response({"error": "Catalog data missing"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        import random
        valid_A = [t for t in data_A.get('titles', []) if t in data_A.get('title_to_full_data', {})]
        valid_B = [t for t in data_B.get('titles', []) if t in data_B.get('title_to_full_data', {})]
        
        t1 = title_A if title_A else random.choice(valid_A[:500])
        t2 = title_B if title_B else random.choice(valid_B[:500])
        
        item1 = data_A['title_to_full_data'].get(t1)
        item2 = data_B['title_to_full_data'].get(t2)
        
        if not item1 or not item2:
            return Response({"error": "Items not found"}, status=status.HTTP_404_NOT_FOUND)
            
        parent_fusion = None
        if parent_id:
            try:
                parent_fusion = CreativeFusion.objects.get(id=parent_id)
            except (CreativeFusion.DoesNotExist, ValueError):
                pass
                
        fusion = CreativeFusion.objects.create(
            title_a=t1, title_b=t2, media_type_a=media_A, media_type_b=media_B,
            chaos_level=chaos_level, universe_balance=universe_balance, art_style=art_style,
            creator=request.user if request.user.is_authenticated else None,
            parent=parent_fusion,
            scenario_text="Génération en cours..."
        )
        
        from .tasks import generate_fusion_scenario_task, generate_fusion_image_task
        from celery import chain
        
        task = chain(
            generate_fusion_scenario_task.s(
                media_type, item1, item2, 
                request.session.get('language', 'Français'), 
                chaos_level=chaos_level, universe_balance=universe_balance, art_style=art_style
            ), 
            generate_fusion_image_task.s(item1, item2, art_style=art_style)
        ).delay()
        
        return Response({
            'fusion_id': fusion.id,
            'task_id': task.id,
            'title_a': t1,
            'title_b': t2,
            'item_a_image': item1.get('image'),
            'item_b_image': item2.get('image')
        })

class ArchetypistTaskStatusView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        task_id = request.query_params.get('task_id')
        fusion_id = request.query_params.get('fusion_id')
        
        if not task_id or not fusion_id:
            return Response({"error": "task_id and fusion_id required"}, status=status.HTTP_400_BAD_REQUEST)
            
        task = AsyncResult(task_id)
        status_msg = "En cours..."
        
        if task.state == 'PENDING':
            status_msg = "En attente de traitement..."
        elif task.state != 'FAILURE':
            if task.info and isinstance(task.info, dict):
                status_msg = task.info.get('status', status_msg)
                
        response_data = {
            'state': task.state,
            'status': status_msg
        }
        
        if task.ready():
            try:
                fusion = CreativeFusion.objects.get(id=fusion_id)
                response_data['scenario'] = fusion.scenario_text
                # Note: 'fusion.image' semble être un URLField dans le modèle, 
                # il faut vérifier s'il existe une méthode ou attribut correct.
                # En attendant, on utilise l'attribut image_url défini dans le modèle.
                response_data['image_url'] = fusion.image_url
                response_data['completed'] = True
            except CreativeFusion.DoesNotExist:
                return Response({"error": "Fusion not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            response_data['completed'] = False
            
        return Response(response_data)

 c l a s s   C o n f i g V i e w ( A P I V i e w ) : 
         p e r m i s s i o n _ c l a s s e s   =   [ p e r m i s s i o n s . A l l o w A n y ] 
 
         d e f   g e t ( s e l f ,   r e q u e s t ) : 
                 d a t a   =   { 
                         ' t h e m e ' :   ' a u t o ' , 
                         ' l a n g u a g e ' :   ' f r ' , 
                         ' u s e r ' :   { 
                                 ' i s _ a u t h e n t i c a t e d ' :   r e q u e s t . u s e r . i s _ a u t h e n t i c a t e d , 
                                 ' u s e r n a m e ' :   r e q u e s t . u s e r . u s e r n a m e   i f   r e q u e s t . u s e r . i s _ a u t h e n t i c a t e d   e l s e   N o n e , 
                                 ' r a n k ' :   g e t a t t r ( r e q u e s t . u s e r ,   ' p r o f i l e ' ,   N o n e )   a n d   r e q u e s t . u s e r . p r o f i l e . r a n k   o r   N o n e , 
                         } , 
                         ' f e a t u r e s ' :   { 
                                 ' E X P E R I M E N T A L _ M O D E S ' :   T r u e , 
                         } 
                 } 
                 r e t u r n   R e s p o n s e ( d a t a ) 
  
 