import base64
import requests
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django_ratelimit.decorators import ratelimit
from ..containers import get_container
from ..session_manager import GameSessionManager
from ..models import GameplaySession
from ..forms import VisionQuestForm
from core.domain.exceptions import InferenceError
import logging

logger = logging.getLogger('animetix')

def spatial_view(request):
    """Vue principale du Spatial Lab (Reconstruction 3D)."""
    container = get_container()
    manager = GameSessionManager(request)
    media_type = manager.get_current_mode()
    data = container.catalog_service.load_data(media_type)
    if not data: return redirect('index')
    
    # On propose quelques exemples de la forge ou du catalogue
    examples = data.get('db', [])[:12]
    return render(request, 'animetix/vision/spatial.html', {
        'examples': examples,
        'media_type': media_type
    })

@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def generate_depth(request):
    """Génère une carte de profondeur pour une image donnée (URL ou Upload)."""
    container = get_container()
    if request.method == 'POST':
        image_url = request.POST.get('image_url')
        uploaded_file = request.FILES.get('image_file')
        
        if not image_url and not uploaded_file:
            return JsonResponse({'error': 'No image provided (URL or File)'}, status=400)
            
        try:
            image_data = None
            display_url = image_url
            
            # 1. Récupération des données binaires
            if uploaded_file:
                image_data = uploaded_file.read()
                display_url = uploaded_file.name
            else:
                res = requests.get(image_url, timeout=10)
                res.raise_for_status()
                image_data = res.content
            
            # 2. Appel au service de Spatial Computing
            depth_map_bytes = container.spatial_computing_service.inference_engine.estimate_depth(image_data)
            
            if not depth_map_bytes:
                return JsonResponse({'error': 'Depth estimation failed'}, status=500)
                
            # 3. Encodage en base64 pour affichage direct (Bypass CORS)
            depth_b64 = base64.b64encode(depth_map_bytes).decode('utf-8')
            original_b64 = base64.b64encode(image_data).decode('utf-8')
            
            return JsonResponse({
                'status': 'success',
                'depth_map': f"data:image/png;base64,{depth_b64}",
                'original_image_b64': f"data:image/jpeg;base64,{original_b64}",
                'original_url': display_url
            })
        except Exception as e:
            logger.error(f"Spatial Depth Error: {e}")
            return JsonResponse({'error': str(e)}, status=500)
            
    return redirect('spatial_lab')

def manga_lab_view(request):
    """Vue principale du Manga Lab (Nettoyage de bulles)."""
    container = get_container()
    data = container.catalog_service.load_data("Manga")
    if not data: return redirect('index')
    
    # Exemples de pages de manga
    examples = data.get('db', [])[:8]
    return render(request, 'animetix/vision/manga_lab.html', {
        'examples': examples
    })

@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def process_manga_bubbles(request):
    """Détecte et nettoie les bulles d'une page de manga."""
    container = get_container()
    if request.method == 'POST':
        image_url = request.POST.get('image_url')
        uploaded_file = request.FILES.get('image_file')
        
        try:
            image_data = None
            if uploaded_file:
                image_data = uploaded_file.read()
            else:
                res = requests.get(image_url, timeout=10)
                res.raise_for_status()
                image_data = res.content
            
            # Pipeline IA : Détection + Inpainting
            result = container.vision_service.inference_engine.process_manga_page(image_data)
            
            original_b64 = base64.b64encode(image_data).decode('utf-8')
            
            return JsonResponse({
                'status': 'success',
                'cleaned_image': result['cleaned_image'],
                'original_image': f"data:image/jpeg;base64,{original_b64}",
                'bubbles_found': len(result['bubbles'])
            })
        except Exception as e:
            logger.error(f"Manga Lab Error: {e}")
            return JsonResponse({'error': str(e)}, status=500)
            
    return redirect('manga_lab')

@ratelimit(key='ip', rate='3/m', method='POST', block=True)
def translate_manga_bubbles(request):
    """Détecte, nettoie et traduit les bulles d'une page de manga."""
    container = get_container()
    if request.method == 'POST':
        image_url = request.POST.get('image_url')
        uploaded_file = request.FILES.get('image_file')
        target_lang = request.session.get('language', 'Français')
        
        try:
            image_data = None
            if uploaded_file:
                image_data = uploaded_file.read()
            else:
                res = requests.get(image_url, timeout=10)
                res.raise_for_status()
                image_data = res.content
            
            # Pipeline IA complet : Détection + Inpainting + OCR + LLM Translate + Draw
            result = container.vision_service.translate_manga_page(image_data, target_lang=target_lang)
            
            if "error" in result:
                return JsonResponse({'error': result["error"]}, status=500)
                
            original_b64 = base64.b64encode(image_data).decode('utf-8')
            
            return JsonResponse({
                'status': 'success',
                'cleaned_image': result['cleaned_image'],
                'translated_image': result['translated_image'],
                'original_image': f"data:image/jpeg;base64,{original_b64}",
                'bubbles_found': len(result['bubbles'])
            })
        except Exception as e:
            logger.error(f"Manga Lab Translation Error: {e}")
            return JsonResponse({'error': str(e)}, status=500)
            
    return redirect('manga_lab')

def vision_quest_view(request):
    container = get_container()
    session = GameSessionManager(request)
    media_type = "Anime"
    data = container.catalog_service.load_data(media_type)
    if not data: return redirect('index')
    
    is_daily = session.get('is_daily', False)
    state = session.get_vision_state()
    
    if not state['secret_id'] or request.GET.get('new') == '1' or is_daily:
        if is_daily:
            secret_title = session.get('secret_title')
            secret = data['title_to_full_data'].get(secret_title)
        else:
            secret = container.vision_quest_service.select_secret(data)
        if not secret: return redirect('index')
        session.start_vision_game(str(secret['id']), secret['title'], secret['image'], media_type)
        if is_daily: session.set('is_daily', True)
        state = session.get_vision_state()

    return render(request, 'animetix/vision/game.html', {
        'guesses': state['guesses'], 
        'best_score': state['best_score'], 
        'game_over': state['game_over'], 
        'secret_image': state['image_url'], 
        'secret_title': state['secret_title'] if state['game_over'] else None, 
        'is_daily': is_daily
    })

@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def vision_quest_guess(request):
    container = get_container()
    session = GameSessionManager(request)
    state = session.get_vision_state()
    if request.method == 'POST' and not state['game_over']:
        form = VisionQuestForm(request.POST)
        if form.is_valid():
            try:
                query, secret_id, secret_title, media_type, is_daily = form.cleaned_data['description'], state['secret_id'], state['secret_title'], state['media_type'], state['is_daily']
                score = container.vision_quest_service.calculate_score(query, secret_id, secret_title, media_type)
                
                guesses = state['guesses']
                guesses.insert(0, {'text': query, 'score': score})
                session.set('vision_guesses', guesses)
                
                if score > state['best_score']: 
                    session.set('vision_best_score', score)
                    
                if container.vision_quest_service.check_victory(score):
                    session.set('vision_game_over', True)
                    if request.user.is_authenticated:
                        try:
                            newly_unlocked = request.user.profile.add_win(is_daily=is_daily, game_mode='vision_quest', media_type=media_type, attempts=len(guesses))
                            session.handle_win_achievements(newly_unlocked)
                        except Exception: pass
                    GameplaySession.objects.create(
                        user=request.user if request.user.is_authenticated else None,
                        game_mode='vision_quest', 
                        media_type=media_type, 
                        target_item=secret_title, 
                        history=guesses, 
                        was_won=True
                    )
            except InferenceError as e:
                logger.error(f"Inference Error in Vision Quest: {e}")
                return JsonResponse({'error': "Le moteur d'IA est temporairement indisponible."}, status=503)
            except Exception as e:
                logger.error(f"Unexpected Error in Vision Quest: {e}")
    return redirect('vision_quest')

