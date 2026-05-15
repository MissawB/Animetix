from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from .services import AnimetixService, LangChainService, BlindTestService, CoverTestService, check_achievements, DIFFICULTY_SETTINGS
from .models import Profile, DailyChallenge, ChallengeResult, Achievement, UserAchievement, GameplaySession, GlobalBoss, BossParticipation, DuelRoom, Friendship
import json
import random
import numpy as np
import os
import hashlib
import datetime
from sklearn.metrics.pairwise import cosine_similarity
import re
from collections import Counter
import requests
import string

from .forms import GameGuessForm, VisionQuestForm, AniminatorForm, AkinetixAnswerForm, CustomConfigForm
from .containers import get_container

# Initialize services
animetix_service = AnimetixService()
blindtest_service = BlindTestService()
covertest_service = CoverTestService()

from core.domain.exceptions import AnimetixError, InferenceError, CatalogNotFoundError

import logging
logger = logging.getLogger('animetix')

try:
    langchain_service = LangChainService()
except Exception as e:
    logger.warning(f"Warning: LangChainService could not be initialized: {e}")
    langchain_service = None

# --- GLOBAL UTILS ---
def get_gaussian_weights(n):
    mu = n * 0.4
    sigma = n * 0.8
    x = np.arange(n)
    weights = np.exp(-0.5 * ((x - mu) / sigma)**2)
    return weights.tolist()

def get_current_mode(request):
    return request.session.get('media_type', 'Anime')

def switch_mode(request, mode):
    if mode in ['Anime', 'Manga', 'Character']:
        request.session['media_type'] = mode
        request.session.modified = True
    return redirect(request.META.get('HTTP_REFERER', 'index'))

def switch_language(request, lang):
    if lang in ['Français', 'English']:
        request.session['language'] = lang
        request.session.modified = True
    return redirect(request.META.get('HTTP_REFERER', 'index'))

def switch_difficulty(request, diff):
    if diff in ['Easy', 'Normal', 'Hard', 'Impossible']:
        request.session['difficulty'] = diff
        request.session.modified = True
    return JsonResponse({'status': 'ok'})

def get_similarity_score(mode, secret_title, guess_title, data=None):
    id_a = data['title_to_full_data'][secret_title]['id']
    id_b = data['title_to_full_data'][guess_title]['id']
    return animetix_service.game_service.calculate_similarity(mode, id_a, id_b)

def calculate_raw_similarity(media_type, secret_title, guess_title, data):
    return animetix_service.game_service.calculate_raw_similarity(media_type, secret_title, guess_title, data)

def handle_win_achievements(request, unlocked_achievements):
    """Stocke les nouveaux succès en session pour affichage Toast."""
    if not unlocked_achievements: return
    new_ach = request.session.get('new_achievements', [])
    for ach in unlocked_achievements:
        new_ach.append({
            'code': ach.code,
            'name': ach.name,
            'icon': ach.icon,
            'xp': ach.xp_reward
        })
    request.session['new_achievements'] = new_ach

def get_game_modes(features=None):
    """Centralise la configuration des modes de jeu pour l'UI, avec support des Feature Flags."""
    features = features or {}
    experimental = features.get('EXPERIMENTAL_MODES', False)

    modes = {
        'solo': [
            {
                "titre": _("Classic Mode"),
                "titre_brush_1": _("CLASSIC"),
                "titre_brush_2": _("MODE"),
                "description": _("Trouvez le titre mystère grâce à la similarité sémantique."),
                "url": "start_game",
                "icon_url": "/static/animetix/img/ui/frieren.png",
                "gradient": "from-blue-600 via-indigo-500 to-blue-400",
                "post_only": True
            },
            {
                "titre": _("Emoji Decode"),
                "titre_brush_1": _("EMOJI"),
                "titre_brush_2": _("DECODE"),
                "description": _("Déchiffrez les symboles pour identifier l'œuvre cachée."),
                "url": "emoji_decode",
                "icon_url": "/static/animetix/img/ui/Shaman_king.png",
                "gradient": "from-orange-600 via-red-500 to-amber-400",
                "post_only": False
            },
            {
                "titre": _("Animinator Oracle"),
                "titre_brush_1": _("ANIMINATOR"),
                "titre_brush_2": _("ORACLE"),
                "description": _("Posez vos questions à l'Oracle pour débusquer le secret."),
                "url": "animinator",
                "icon_url": "/static/animetix/img/ui/Sinbad.png",
                "gradient": "from-purple-700 via-violet-600 to-purple-400",
                "post_only": False
            },
            {
                "titre": _("Akinetix Devin"),
                "titre_brush_1": _("AKINETIX"),
                "titre_brush_2": _("DEVIN"),
                "description": _("L'IA analyse vos pensées pour deviner ce que vous cachez."),
                "url": "akinetix",
                "icon_url": "/static/animetix/img/ui/Saiki.png",
                "gradient": "from-pink-600 via-rose-500 to-pink-400",
                "post_only": False
            },
            {
                "titre": _("Paradox Quest"),
                "titre_brush_1": _("PARADOX"),
                "titre_brush_2": _("QUEST"),
                "description": _("Débusquez l'intrus parmi les scénarios générés par l'IA."),
                "url": "paradox",
                "icon_url": "/static/animetix/img/ui/Steins_gate.png",
                "gradient": "from-red-700 via-rose-600 to-red-400",
                "post_only": True
            },
            {
                "titre": _("Vision Quest"),
                "titre_brush_1": _("VISION"),
                "titre_brush_2": _("QUEST"),
                "description": _("Défiez la reconnaissance visuelle de l'IA en décrivant l'image."),
                "url": "vision_quest",
                "icon_url": "/static/animetix/img/ui/SAO.png",
                "gradient": "from-cyan-600 via-blue-500 to-sky-400",
                "post_only": False
            },
            {
                "titre": _("Blind Test"),
                "titre_brush_1": _("BLIND"),
                "titre_brush_2": _("TEST"),
                "description": _("Devinez l'animé à partir de son opening ou ending."),
                "url": "blindtest",
                "icon_url": "/static/animetix/img/ui/Kaori.png",
                "gradient": "from-green-600 via-teal-500 to-emerald-400",
                "post_only": True
            },
            {
                "titre": _("Cover Test"),
                "titre_brush_1": _("COVER"),
                "titre_brush_2": _("TEST"),
                "description": _("Devinez le manga à partir de sa couverture (JA/FR)."),
                "url": "covertest",
                "icon_url": "/static/animetix/img/ui/Bakuman.png",
                "gradient": "from-amber-600 via-yellow-500 to-orange-400",
                "post_only": True
            },
        ],
        'multi': [
            {"titre": _("Undercover"), "description": _("Débusquez l'intrus."), "url": "undercover_party_setup", "icon_url": "/static/animetix/img/ui/Light.png", "is_new": False, "post_only": False},
            {"titre": _("Code Manga"), "description": _("Agents secrets."), "url": "codemanga", "icon_url": "/static/animetix/img/ui/code_manga.png", "is_new": False, "post_only": False},
        ],
        'creative': [
            {
                "titre": _("Fusion d'Univers"),
                "titre_sub": _("CRÉEZ DES MONDES UNIQUES À TOUT MOMENT"),
                "url": "archetypist",
                "fusion_image": "/static/animetix/img/ui/Fusion.png",
                "post_only": False
            },
        ],
        'collections': [
            {"nom": "ANIME", "mode": "Anime", "image": "/static/animetix/img/anime.png"},
            {"nom": "MANGA", "mode": "Manga", "image": "/static/animetix/img/manga.png"},
            {"nom": "PERSO", "mode": "Character", "image": "/static/animetix/img/perso.png"},
        ]
    }

    if not experimental:
        modes['solo'] = [m for m in modes['solo'] if m['url'] not in ['paradox', 'vision_quest', 'akinetix']]
        modes['creative'] = []

    # Ajout des modes expérimentaux si activés
    if features.get('BETA_SOCIAL'):
        modes['multi'].append({
            "titre": _("Duels 1vs1"), 
            "description": _("Affrontez un ami en temps réel."), 
            "url": "join_duel", 
            "icon_url": "/static/animetix/img/ui/Naruto_Sasuke.png", 
            "is_new": True, 
            "post_only": False
        })
        
    return modes

# --- VIEWS ---

def index(request):
    mode = get_current_mode(request)
    profile = request.user.profile if request.user.is_authenticated else None
    
    # Sélection aléatoire de l'image de héros
    home_images = ["Dio.png", "Gintama.png", "Mugiwara.png", "Team_7.png", "Z_team.png"]
    random_hero = random.choice(home_images)

    # Récupération des modes via la configuration centralisée
    from django.conf import settings
    config = get_game_modes(getattr(settings, 'FEATURE_FLAGS', {}))

    context = {
        'current_mode': mode,
        'profile': profile,
        'modes_solo': config['solo'],
        'modes_multi': config['multi'],
        'modes_creative': config['creative'],
        'media_collections': config['collections'],
        'hero_image': random_hero,
    }
    return render(request, 'animetix/index.html', context)

def start_daily_challenge(request):
    media_type = get_current_mode(request)
    today = datetime.date.today()
    daily, created = DailyChallenge.objects.get_or_create(date=today, defaults={'media_type': media_type, 'secret_title': '', 'game_mode': 'classic'})
    data = animetix_service.load_data(media_type)
    if not data: return redirect('index')
    
    if created or not daily.secret_title:
        seed = int(hashlib.md5(f"{today}{media_type}".encode()).hexdigest(), 16)
        random.seed(seed)
        
        # Featured mode of the day
        modes = ['classic', 'emoji', 'animinator', 'akinetix', 'paradox', 'vision_quest', 'blindtest', 'covertest']
        daily.game_mode = random.choice(modes)
        
        valid_titles = [item.get('title') or item.get('name') for item in data['db']]
        if not valid_titles:
            return redirect('index')
        daily.secret_title = random.choice(valid_titles[:500])
        daily.save()
        random.seed(None)
    
    # On marque la session
    request.session.update({
        'is_daily': True,
        'daily_id': daily.id,
        'secret_title': daily.secret_title,
        'media_type': media_type,
        'game_over': False
    })
    
    mode_param = request.GET.get('mode')
    if mode_param:
        if mode_param == 'emoji': return redirect('emoji_decode')
        elif mode_param == 'animinator': return redirect('animinator')
        elif mode_param == 'akinetix': return redirect('akinetix')
        elif mode_param == 'paradox': return redirect('paradox')
        elif mode_param == 'vision_quest': return redirect('vision_quest')
        elif mode_param == 'blindtest': return redirect('blindtest')
        elif mode_param == 'covertest': return redirect('covertest')
        elif mode_param == 'classic': return start_game(request, override_secret=daily.secret_title)
    
    # Si pas de mode spécifié, on affiche la page de sélection
    completed = False
    if request.user.is_authenticated:
        completed = ChallengeResult.objects.filter(user=request.user, challenge=daily).exists()
    
    modes_daily = [
        {
            "id": "classic",
            "brush1": "CLASSIC",
            "brush2": "MODE",
            "description": "Trouvez le titre mystère du jour via la similarité.",
            "icon": "/static/animetix/img/ui/frieren.png",
            "gradient": "from-blue-600 via-indigo-500 to-blue-400",
            "completed": completed
        },
        {
            "id": "emoji",
            "brush1": "EMOJI",
            "brush2": "DECODE",
            "description": "Déchiffrez l'œuvre derrière les emojis du jour.",
            "icon": "/static/animetix/img/ui/Shaman_king.png",
            "gradient": "from-orange-600 via-red-500 to-amber-400",
            "completed": completed
        },
        {
            "id": "animinator",
            "brush1": "ANIMINATOR",
            "brush2": "ORACLE",
            "description": "Posez vos questions à l'Oracle pour débusquer le secret.",
            "icon": "/static/animetix/img/ui/Sinbad.png",
            "gradient": "from-purple-700 via-violet-600 to-purple-400",
            "completed": completed
        },
        {
            "id": "akinetix",
            "brush1": "AKINETIX",
            "brush2": "DEVIN",
            "description": "L'IA tente de deviner à quelle œuvre du jour vous pensez.",
            "icon": "/static/animetix/img/ui/Saiki.png",
            "gradient": "from-pink-600 via-rose-500 to-pink-400",
            "completed": completed
        },
        {
            "id": "paradox",
            "brush1": "PARADOX",
            "brush2": "QUEST",
            "description": "Débusquez l'intrus parmi les propositions du jour.",
            "icon": "/static/animetix/img/ui/Steins_gate.png",
            "gradient": "from-red-700 via-rose-600 to-red-400",
            "completed": completed
        },
        {
            "id": "vision_quest",
            "brush1": "VISION",
            "brush2": "QUEST",
            "description": "Décrivez l'image mystère du jour.",
            "icon": "/static/animetix/img/ui/SAO.png",
            "gradient": "from-cyan-600 via-blue-500 to-sky-400",
            "completed": completed
        },
        {
            "id": "blindtest",
            "brush1": "BLIND",
            "brush2": "TEST",
            "description": "Devinez l'animé du jour à partir de son opening/ending.",
            "icon": "/static/animetix/img/ui/Kaori.png",
            "gradient": "from-green-600 via-teal-500 to-emerald-400",
            "completed": completed
        },
        {
            "id": "covertest",
            "brush1": "COVER",
            "brush2": "TEST",
            "description": "Devinez le manga du jour à partir de sa couverture.",
            "icon": "/static/animetix/img/ui/Bakuman.png",
            "gradient": "from-amber-600 via-yellow-500 to-orange-400",
            "completed": completed
        },
    ]

    from django.conf import settings
    experimental = getattr(settings, 'FEATURE_FLAGS', {}).get('EXPERIMENTAL_MODES', False)
    if not experimental:
        modes_daily = [m for m in modes_daily if m['id'] not in ['paradox', 'vision_quest', 'akinetix']]

    context = {
        'date': today,
        'media_type': media_type,
        'modes': modes_daily,
    }
    return render(request, 'animetix/daily_selection.html', context)

def custom_config_view(request):
    """Affiche la page de configuration du mode personnalisé avec genres et tags."""
    media_type = get_current_mode(request)
    data = animetix_service.load_data(media_type)
    
    # Extraire tous les genres et tags uniques de la DB
    all_genres = set()
    all_tags = set()
    if data:
        for item in data['db']:
            all_genres.update(item.get('genres', []))
            all_tags.update(item.get('tags', []))
            
    context = {
        'whitelist': request.session.get('custom_whitelist', []),
        'blacklist': request.session.get('custom_blacklist', []),
        'genres_white': request.session.get('custom_genres_white', []),
        'genres_black': request.session.get('custom_genres_black', []),
        'tags_white': request.session.get('custom_tags_white', []),
        'tags_black': request.session.get('custom_tags_black', []),
        'mode': request.session.get('custom_mode', 'all'),
        'all_genres': sorted(list(all_genres)),
        'all_tags': sorted(list(all_tags))
    }
    return render(request, 'animetix/custom_config.html', context)

def save_custom_config(request):
    """Sauvegarde la configuration personnalisée complète."""
    if request.method == 'POST':
        request.session.update({
            'custom_whitelist': request.POST.getlist('whitelist'),
            'custom_blacklist': request.POST.getlist('blacklist'),
            'custom_genres_white': request.POST.getlist('genres_white'),
            'custom_genres_black': request.POST.getlist('genres_black'),
            'custom_tags_white': request.POST.getlist('tags_white'),
            'custom_tags_black': request.POST.getlist('tags_black'),
            'custom_mode': request.POST.get('mode', 'all'),
            'difficulty': 'Custom'
        })
        request.session.modified = True
        return start_game(request)
    return redirect('custom_config')

def start_game(request, override_secret=None):
    media_type, difficulty = get_current_mode(request), request.session.get('difficulty', 'Normal')
    data = animetix_service.load_data(media_type)
    if not data: return redirect('index')
    
    if override_secret: 
        secret_title = override_secret
    else:
        request.session['is_daily'], request.session['is_ranked'] = False, False
        
        if difficulty == 'Custom':
            # Utilisation de la logique centralisée dans le domaine pour le mode personnalisé
            config = {
                'mode': request.session.get('custom_mode', 'all'),
                'whitelist': request.session.get('custom_whitelist', []),
                'blacklist': request.session.get('custom_blacklist', []),
                'genres_white': request.session.get('custom_genres_white', []),
                'genres_black': request.session.get('custom_genres_black', []),
                'tags_white': request.session.get('custom_tags_white', []),
                'tags_black': request.session.get('custom_tags_black', []),
            }
            secret_title = animetix_service.game_service.select_secret_custom(media_type, config, data)
        else:
            # Domain-driven selection for standard difficulties
            secret_title = animetix_service.game_service.select_secret(media_type, difficulty, DIFFICULTY_SETTINGS)

    if not secret_title: return redirect('index')

    request.session.update({'secret_title': secret_title, 'max_raw_sim': 0.8, 'difficulty': difficulty, 'media_type': media_type, 'guesses': [], 'game_over': False, 'revealed_hints': []})
    request.session.modified = True
    return redirect('game')

def start_ranked_mode(request):
    request.session['is_ranked'], request.session['is_daily'] = True, False
    return ranked_next_level(request)

def ranked_next_level(request):
    if not request.session.get('is_ranked'): return redirect('index')
    media_type = get_current_mode(request); data = animetix_service.load_data(media_type)
    points = request.user.profile.ranked_points if request.user.is_authenticated else 0
    # DIFFICULTÉ LINÉAIRE : On élargit le pool de recherche tous les 10 points
    # Start: 100, Point 1000: pool 600, Point 5000: pool 2600
    rank_limit = min(2500, 100 + int(points / 2))
    valid_lookup = data.get('lookup', [])[:rank_limit]
    valid_titles = [item.get('title') or item.get('name') for item in valid_lookup if (item.get('title') or item.get('name')) in data.get('title_to_full_data', {})]
    
    if not valid_titles:
        # Fallback to general titles from db if lookup is empty or out of sync
        valid_titles = data.get('titles', [])[:100]
        
    if not valid_titles:
        # If still empty, we can't play this mode
        return redirect('index')

    secret_title = random.choice(valid_titles)
    request.session.update({'secret_title': secret_title, 'max_raw_sim': 0.8, 'media_type': media_type, 'guesses': [], 'game_over': False, 'revealed_hints': []})
    request.session.modified = True
    return redirect('game')

# --- IMMERSION UTILS ---
def get_theme_color(title):
    """Retourne une couleur d'accentuation basée sur le titre ou la série."""
    title = title.lower()
    mapping = {
        'naruto': '#FF9800', # Orange
        'one piece': '#FBC02D', # Yellow
        'bleach': '#FF5722', # Orange-Red
        'hunter x hunter': '#4CAF50', # Green
        'dragon ball': '#0277BD', # Blue
        'attack on titan': '#795548', # Brown
        'death note': '#212121', # Black
        'demon slayer': '#E91E63', # Pink/Red
        'jujutsu kaisen': '#673AB7', # Purple
        'frieren': '#80CBC4', # Soft Teal
        'mushoku': '#AFB42B', # Moss Green
    }
    for key, color in mapping.items():
        if key in title: return color
    return '#fdb913' # Default Yellow

def game_view(request):
    media_type = request.session.get('media_type', 'Anime'); data = animetix_service.load_data(media_type)
    if not data or 'secret_title' not in request.session: return redirect('index')
    guessed_titles = [g['title'] for g in request.session.get('guesses', [])]
    secret_title = request.session.get('secret_title'); secret_data = data['title_to_full_data'].get(secret_title)
    if not secret_data: return redirect('index')
    
    theme_color = get_theme_color(secret_title)
    
    hints = {k: {'revealed': k in request.session.get('revealed_hints', []), 'locked': True} for k in ['poster', 'character', 'culture', 'rec', 'sim', 'chars', 'origin', 'words', 'vibe']}
    hints['poster'] = {'revealed': 'poster' in request.session.get('revealed_hints', []), 'value': secret_data.get('image'), 'locked': False}
    
    return render(request, 'animetix/classic/game.html', {
        'media_type': media_type, 'guesses': request.session.get('guesses', []), 'game_over': request.session.get('game_over', False),
        'guess_count': len(guessed_titles), 'hints': hints, 'radar_data': json.dumps([]), 
        'is_daily': request.session.get('is_daily', False), 'is_ranked': request.session.get('is_ranked', False),
        'ranked_points': request.user.profile.ranked_points if request.user.is_authenticated else 0,
        'secret_title': secret_title if request.session.get('game_over') else None, 'secret_data': secret_data if request.session.get('game_over') else None,
        'remaining_items': [item for item in data['lookup'] if item['title'] in data['title_to_full_data']],
        'theme_color': theme_color
    })

# --- MODE 3 : VISION QUEST (Multimodal CLIP) ---

def vision_quest_view(request):
    media_type = "Anime" # Limité aux animes pour le moment
    data = animetix_service.load_data(media_type)
    if not data: return redirect('index')

    is_daily = request.session.get('is_daily', False)
    
    if 'vision_secret_id' not in request.session or request.GET.get('new') == '1' or is_daily:
        if is_daily:
            secret_title = request.session.get('secret_title')
            secret = data['title_to_full_data'].get(secret_title)
        else:
            secret = animetix_service.vision_quest_service.select_secret(data)
        
        if not secret: return redirect('index')

        request.session.update({
            'vision_media_type': media_type,
            'vision_secret_id': str(secret['id']),
            'vision_secret_title': secret['title'],
            'vision_secret_image': secret['image'],
            'vision_guesses': [],
            'vision_game_over': False,
            'vision_best_score': 0.0
        })

    return render(request, 'animetix/vision/game.html', {
        'guesses': request.session.get('vision_guesses'),
        'best_score': request.session.get('vision_best_score'),
        'game_over': request.session.get('vision_game_over'),
        'secret_image': request.session.get('vision_secret_image'),
        'secret_title': request.session.get('vision_secret_title') if request.session.get('vision_game_over') else None,
        'is_daily': is_daily
    })

from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def vision_quest_guess(request):
    if request.method == 'POST' and not request.session.get('vision_game_over'):
        form = VisionQuestForm(request.POST)
        if form.is_valid():
            try:
                query = form.cleaned_data['description']
                secret_id = request.session.get('vision_secret_id')
                secret_title = request.session.get('vision_secret_title')
                media_type = request.session.get('vision_media_type', 'Anime')
                is_daily = request.session.get('is_daily', False)

                # Calcul de score via le Domaine
                score = animetix_service.vision_quest_service.calculate_score(
                    query, secret_id, secret_title, media_type
                )
                
                guesses = request.session.get('vision_guesses', [])
                guesses.insert(0, {'text': query, 'score': score})
                request.session['vision_guesses'] = guesses
                
                if score > request.session.get('vision_best_score', 0):
                    request.session['vision_best_score'] = score
                
                if animetix_service.vision_quest_service.check_victory(score):
                    request.session['vision_game_over'] = True
                    if request.user.is_authenticated:
                        newly_unlocked = request.user.profile.add_win(
                            is_daily=is_daily,
                            game_mode='vision_quest',
                            media_type=media_type,
                            attempts=len(guesses)
                        )
                        handle_win_achievements(request, newly_unlocked)
                    
                    GameplaySession.objects.create(
                        game_mode='vision_quest',
                        media_type=media_type,
                        target_item=secret_title,
                        history=guesses,
                        was_won=True
                    )
                request.session.modified = True
            except InferenceError as e:
                logger.error(f"Inference Error in Vision Quest: {e}")
                return JsonResponse({'error': "Le moteur d'IA est temporairement indisponible."}, status=503)
            except Exception as e:
                logger.error(f"Unexpected Error in Vision Quest: {e}")
                
    return redirect('vision_quest')

def make_guess(request):
    if request.method == 'POST' and not request.session.get('game_over'):
        form = GameGuessForm(request.POST)
        if form.is_valid():
            try:
                guess_title = form.cleaned_data['guess']
                media_type = get_current_mode(request)
                secret_title = request.session.get('secret_title')
                max_sim = request.session.get('max_raw_sim', 1.0)
                data = animetix_service.load_data(media_type)
                
                if not data or guess_title not in data['title_to_index']: 
                    return redirect('game')
                
                # Utilisation du Domaine pour la similarité brute
                raw_sim = animetix_service.game_service.calculate_raw_similarity(
                    media_type, secret_title, guess_title, data
                )
                
                # VÉRIFICATION INTELLIGENTE DU TITRE (SMART MATCH)
                secret_item = data['title_to_full_data'].get(secret_title)
                is_correct = animetix_service.game_service.check_title_match(guess_title, secret_item)
                
                score = 100.0 if is_correct else round(min(0.99, (raw_sim / max_sim) * 0.99) * 100, 2)
                color = "danger" if score > 90 else "warning" if score > 70 else "primary" if score > 40 else "secondary"
                
                guesses = request.session.get('guesses', [])
                g_data = data['title_to_full_data'].get(guess_title, {})
                guesses.append({
                    "title": guess_title, 
                    "title_english": g_data.get('title_english'), 
                    "title_native": g_data.get('title_native'), 
                    "image": g_data.get('image'), 
                    "score": score, 
                    "color": color
                })
                guesses.sort(key=lambda x: x['score'], reverse=True)
                request.session['guesses'] = guesses
                
                if is_correct:
                    request.session['game_over'] = True
                    if request.user.is_authenticated:
                        item_rank = 100
                        for i, item in enumerate(data['lookup']):
                            if (item.get('title') or item.get('name')) == secret_title:
                                item_rank = i + 1; break
                        newly_unlocked = request.user.profile.add_win(
                            is_daily=request.session.get('is_daily', False), 
                            is_ranked=request.session.get('is_ranked', False), 
                            item_rank=item_rank,
                            game_mode='classic',
                            media_type=media_type,
                            attempts=len(guesses)
                        )
                        handle_win_achievements(request, newly_unlocked)
                    
                    GameplaySession.objects.create(
                        user=request.user if request.user.is_authenticated else None,
                        game_mode='classic',
                        media_type=media_type,
                        target_item=secret_title,
                        history=guesses,
                        was_won=True
                    )
                request.session.modified = True
            except AnimetixError as e:
                logger.error(f"Domain Error in Classic Guess: {e}")
    return redirect('game')

def leaderboard_view(request):
    top_profiles = Profile.objects.select_related('user').order_by('-ranked_points')[:20]
    return render(request, 'animetix/leaderboard.html', {'top_profiles': top_profiles})

def achievements_view(request):
    all_ach = Achievement.objects.all(); unlocked = UserAchievement.objects.filter(user=request.user).values_list('achievement_id', flat=True) if request.user.is_authenticated else []
    return render(request, 'animetix/achievements.html', {'all_achievements': all_ach, 'unlocked_ids': list(unlocked)})

def emoji_decode_view(request):
    media_type, data = get_current_mode(request), animetix_service.load_data(get_current_mode(request))
    if not data: return redirect('index')
    
    if request.GET.get('new') == '1': 
        request.session['is_daily'] = False
        request.session['is_ranked'] = False
        
    is_daily, is_ranked = request.session.get('is_daily', False), request.session.get('is_ranked', False)
    
    if 'emoji_secret' not in request.session or request.GET.get('new') == '1' or is_daily or is_ranked:
        if is_daily or is_ranked: 
            secret = request.session.get('secret_title')
        else:
            secret = animetix_service.emoji_service.select_secret(data)
            
        if not secret: return redirect('index')
            
        # Utilisation du service de domaine pour générer les emojis via LLM
        emoji_list = animetix_service.emoji_service.generate_emojis(
            media_type, secret, data['title_to_full_data'][secret].get('description', '')
        )

        request.session.update({
            'emoji_secret': secret, 
            'emoji_list': emoji_list, 
            'emoji_guesses': [], 
            'emoji_game_over': False
        })
        if is_daily: request.session['is_daily'] = True
        if is_ranked: request.session['is_ranked'] = True
    
    # Préparation autocomplétion
    remaining_items = []
    for item in data['db']:
        remaining_items.append({
            't': item.get('title'),
            'en': item.get('title_english'),
            'jp': item.get('title_native'),
            'i': item.get('image')
        })

    return render(request, 'animetix/emoji/game.html', {
        'media_type': media_type, 
        'emojis': request.session.get('emoji_list'), 
        'guesses': request.session.get('emoji_guesses', []), 
        'game_over': request.session.get('emoji_game_over', False), 
        'is_daily': is_daily, 
        'is_ranked': is_ranked, 
        'ranked_points': request.user.profile.ranked_points if request.user.is_authenticated else 0, 
        'remaining_items': remaining_items,
        'secret_title': request.session.get('emoji_secret') if request.session.get('emoji_game_over') else None
    })

def emoji_decode_guess(request):
    if request.method == 'POST' and not request.session.get('emoji_game_over'):
        form = GameGuessForm(request.POST)
        if form.is_valid():
            guess_title = form.cleaned_data['guess']
            secret, media_type = request.session.get('emoji_secret'), get_current_mode(request)
            data = animetix_service.load_data(media_type)
            guesses = request.session.get('emoji_guesses', [])
            
            # Récupération des infos complètes du guess
            guess_full = data['title_to_full_data'].get(guess_title)
            secret_item = data['title_to_full_data'].get(secret)
            
            if guess_full:
                # VÉRIFICATION INTELLIGENTE (SMART MATCH)
                is_correct = animetix_service.game_service.check_title_match(guess_title, secret_item)
                
                guesses.append({
                    'title': guess_title,
                    'title_en': guess_full.get('title_english'),
                    'title_jp': guess_full.get('title_native'),
                    'image': guess_full.get('image'),
                    'is_correct': is_correct
                })
                request.session['emoji_guesses'] = guesses
                
                if is_correct: 
                    request.session['emoji_game_over'] = True
                    if request.user.is_authenticated:
                        item_rank = 100
                        for i, item in enumerate(data['lookup']):
                            if (item.get('title') or item.get('name')) == secret: item_rank = i + 1; break
                        newly_unlocked = request.user.profile.add_win(
                            is_daily=request.session.get('is_daily', False), 
                            is_ranked=request.session.get('is_ranked', False), 
                            item_rank=item_rank,
                            game_mode='emoji',
                            media_type=media_type,
                            attempts=len(guesses)
                        )
                        handle_win_achievements(request, newly_unlocked)
                    
                    GameplaySession.objects.create(
                        user=request.user if request.user.is_authenticated else None,
                        game_mode='emoji',
                        media_type=media_type,
                        target_item=secret,
                        history=guesses,
                        was_won=True
                    )
                request.session.modified = True
    return redirect('emoji_decode')

def animinator_view(request):
    media_type, data = get_current_mode(request), animetix_service.load_data(get_current_mode(request))
    if not data: return redirect('index')
    
    if request.GET.get('new') == '1': request.session['is_daily'] = False
    is_daily = request.session.get('is_daily', False)
    
    if 'animinator_secret' not in request.session or request.GET.get('new') == '1' or is_daily:
        if is_daily:
            secret = request.session.get('secret_title')
        else:
            secret = animetix_service.animinator_service.select_secret(data)
            
        if not secret: return redirect('index')

        request.session.update({
            'animinator_secret': secret, 
            'animinator_chat': [], 
            'animinator_questions_left': 20, 
            'animinator_game_over': False
        })
        if is_daily: request.session['is_daily'] = True
        
    return render(request, 'animetix/animinator/animinator.html', {
        'media_type': media_type, 
        'chat': request.session.get('animinator_chat', []), 
        'questions_left': request.session.get('animinator_questions_left', 20), 
        'game_over': request.session.get('animinator_game_over', False), 
        'is_daily': is_daily, 
        'secret_title': request.session.get('animinator_secret') if request.session.get('animinator_game_over') else None, 
        'remaining_items': [item for item in data['lookup'] if item['title'] in data['title_to_full_data']]
    })

@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def animinator_ask(request):
    if request.method == 'POST' and not request.session.get('animinator_game_over'):
        form = AniminatorForm(request.POST)
        if form.is_valid():
            try:
                question = form.cleaned_data['question']
                media_type, data = get_current_mode(request), animetix_service.load_data(get_current_mode(request))
                secret = request.session.get('animinator_secret')
                
                if not data or secret not in data['title_to_full_data']:
                    return redirect('index')
                    
                answer = animetix_service.animinator_service.ask_oracle(
                    media_type, secret, data['title_to_full_data'][secret], question
                )
                
                chat = request.session.get('animinator_chat', [])
                chat.append({'q': question, 'a': answer})
                request.session['animinator_chat'] = chat
                
                q_left = request.session.get('animinator_questions_left', 20) - 1
                request.session['animinator_questions_left'] = q_left
                
                if q_left <= 0:
                    request.session['animinator_game_over'] = True
                    GameplaySession.objects.create(
                        game_mode='animinator',
                        media_type=media_type,
                        target_item=secret,
                        history=chat,
                        was_won=False
                    )
                request.session.modified = True
            except InferenceError as e:
                logger.error(f"Inference Error in Animinator: {e}")
            except Exception as e:
                logger.error(f"Unexpected Error in Animinator: {e}")
                
    return redirect('animinator')

def animinator_guess(request):
    if request.method == 'POST' and not request.session.get('animinator_game_over'):
        form = GameGuessForm(request.POST)
        if form.is_valid():
            try:
                guess = form.cleaned_data['guess']
                secret = request.session.get('animinator_secret')
                media_type = get_current_mode(request)
                data = animetix_service.load_data(media_type)
                
                # VÉRIFICATION INTELLIGENTE (SMART MATCH)
                secret_item = data['title_to_full_data'].get(secret)
                is_correct = animetix_service.game_service.check_title_match(guess, secret_item)
                
                if is_correct:
                    request.session['animinator_game_over'] = True
                    if request.user.is_authenticated: 
                        newly_unlocked = request.user.profile.add_win(
                            is_daily=request.session.get('is_daily', False),
                            game_mode='animinator',
                            media_type=media_type,
                            attempts=len(request.session.get('animinator_chat', []))
                        )
                        handle_win_achievements(request, newly_unlocked)
                    
                    GameplaySession.objects.create(
                        game_mode='animinator',
                        media_type=media_type,
                        target_item=secret,
                        history=request.session.get('animinator_chat', []),
                        was_won=True
                    )
                request.session.modified = True
            except Exception as e:
                logger.error(f"Error in Animinator Guess: {e}")
    return redirect('animinator')

def akinetix_view(request):
    media_type, data = get_current_mode(request), animetix_service.load_data(get_current_mode(request))
    if not data: return redirect('index')
    
    if request.GET.get('new') == '1': 
        request.session['akinetix_probs'] = None
        request.session['akinetix_asked_attrs'] = None
        request.session['is_daily'] = False
    is_daily = request.session.get('is_daily', False)
    
    if 'akinetix_current_q' not in request.session or request.GET.get('new') == '1' or is_daily:
        game_state = get_container().akinetix_service.start_new_game(data['db'])
        request.session.update({
            'akinetix_history': game_state['history'], 
            'akinetix_current_q': game_state['current_q'], 
            'akinetix_current_attr': game_state['current_attr'],
            'akinetix_game_over': game_state['game_over'], 
            'akinetix_ai_guess': game_state['ai_guess'],
            'akinetix_probs': game_state['probs'],
            'akinetix_asked_attrs': game_state['asked_attrs']
        })
        if is_daily: request.session['is_daily'] = True
        
    return render(request, 'animetix/akinetix/akinetix.html', {
        'media_type': media_type, 
        'current_question': request.session.get('akinetix_current_q'), 
        'history': request.session.get('akinetix_history'), 
        'game_over': request.session.get('akinetix_game_over'), 
        'ai_guess': request.session.get('akinetix_ai_guess'),
        'is_daily': is_daily
    })

def akinetix_answer(request):
    if request.method == 'POST' and not request.session.get('akinetix_game_over'):
        form = AkinetixAnswerForm(request.POST)
        raw_answer = "NE SAIT PAS"
        if form.is_valid():
            raw_answer = form.cleaned_data['answer']
        
        media_type = get_current_mode(request)
        data = animetix_service.load_data(media_type)
        if not data: return redirect('index')

        state = {
            'probs': request.session.get('akinetix_probs'),
            'asked_attrs': request.session.get('akinetix_asked_attrs'),
            'current_attr': request.session.get('akinetix_current_attr'),
            'current_q': request.session.get('akinetix_current_q'),
            'history': request.session.get('akinetix_history', [])
        }
        
        new_state = get_container().akinetix_service.process_answer(data['db'], state, raw_answer)
        
        request.session.update({
            'akinetix_history': new_state['history'],
            'akinetix_current_q': new_state['current_q'],
            'akinetix_current_attr': new_state['current_attr'],
            'akinetix_game_over': new_state['game_over'],
            'akinetix_ai_guess': new_state['ai_guess'],
            'akinetix_probs': new_state['probs'],
            'akinetix_asked_attrs': new_state['asked_attrs']
        })
        request.session.modified = True
        
    return redirect('akinetix')

def akinetix_confirm(request):
    """Confirm if the AI guess in Akinetix was correct and save session."""
    if request.method == 'POST':
        is_correct = request.POST.get('correct') == 'true'
        media_type = get_current_mode(request)
        history = request.session.get('akinetix_history', [])
        ai_guess = request.session.get('akinetix_ai_guess')
        is_daily = request.session.get('is_daily', False)
        
        # Pour Akinetix, si l'humain gagne (l'IA a tort), on récompense
        if not is_correct and request.user.is_authenticated:
            newly_unlocked = request.user.profile.add_win(is_daily=is_daily, game_mode='akinetix')
            handle_win_achievements(request, newly_unlocked)

        GameplaySession.objects.create(
            game_mode='akinetix',
            media_type=media_type,
            target_item=ai_guess or "Unknown",
            history=history,
            was_won=is_correct # was_won pour Akinetix signifie que l'IA a vu juste
        )
    return redirect('akinetix', new='1')

from django.http import JsonResponse, HttpResponse
from celery.result import AsyncResult

def get_task_status(request, task_id):
    """Vérifie l'état d'une tâche Celery et retourne le résultat si terminé."""
    try:
        res = AsyncResult(task_id)
        if res.ready():
            result = res.result
            # Si c'est un résultat de fusion (dict)
            if isinstance(result, dict) and 'scenario' in result:
                return render(request, 'animetix/archetypist/archetypist_result_fragment.html', {
                    'reasoning': result.get('reasoning'),
                    'scenario': result.get('scenario'),
                    'fusion_image': result.get('fusion_image'),
                    'item_A': request.session.get('temp_item_A'), 
                    'item_B': request.session.get('temp_item_B'),
                })
            return JsonResponse({'ready': True, 'result': result})
    except Exception as e:
        logger.error(f"⚠️ Celery Result Backend Error: {e}")
        return HttpResponse(status=204) # Ne rien changer si erreur backend
    
    # 204 No Content : Indique à HTMX de ne PAS faire le swap (garde le loader)
    return HttpResponse(status=204)

from .presenters import ArchetypistPresenter

def archetypist_view(request):
    media_type = get_current_mode(request)
    difficulty = request.session.get('difficulty', 'Normal')
    data = animetix_service.load_data(media_type)
    
    if not data:
        logger.error(f"❌ Archetypist Error: Data for {media_type} not loaded")
        return redirect('index')

    # Définition des options de mélange (cross-media) via le Presenter
    cross_options = ArchetypistPresenter.get_cross_media_options(media_type)

    # On ne lance la fusion que si on a les titres ou si on demande un replay
    if (request.method == 'POST' and request.POST.get('title_A')) or request.GET.get('replay') == '1':
        title_A, title_B = request.POST.get('title_A'), request.POST.get('title_B')
        media_A = request.POST.get('media_type_A', media_type)
        media_B = request.POST.get('media_type_B', media_type)
        
        data_A = animetix_service.load_data(media_A) if media_A != media_type else data
        data_B = animetix_service.load_data(media_B) if media_B != media_type else data
        
        if not data_A or not data_B: return redirect('index')
        
        valid_A = [t for t in data_A.get('titles', []) if t in data_A.get('title_to_full_data', {})]
        valid_B = [t for t in data_B.get('titles', []) if t in data_B.get('title_to_full_data', {})]
        
        if not valid_A or not valid_B: return redirect('index')
        
        t1 = title_A if title_A else random.choice(valid_A[:500])
        t2 = title_B if title_B else random.choice(valid_B[:500])
        
        item1, item2 = data_A['title_to_full_data'].get(t1), data_B['title_to_full_data'].get(t2)
        if not item1 or not item2: return redirect('index')
        
        # On stocke temporairement les items en session pour le fragment final
        request.session['temp_item_A'] = item1
        request.session['temp_item_B'] = item2
        
        # --- LANCEMENT ASYNC CELERY (CHAINÉ) ---
        from celery import chain
        from .tasks import generate_fusion_scenario_task, generate_fusion_image_task
        
        task_chain = chain(
            generate_fusion_scenario_task.s(media_type, item1, item2, request.session.get('language', 'Français')),
            generate_fusion_image_task.s(item1, item2)
        )
        task = task_chain.delay()
        
        if request.headers.get('HX-Request'):
            return render(request, 'animetix/archetypist/archetypist_loading_fragment.html', {'task_id': task.id})
        
        return render(request, 'animetix/archetypist/archetypist.html', {
            'task_id': task.id, 
            'media_type': media_type,
            'item_A': item1,
            'item_B': item2,
            'show_titles': True
        })

    # Mode GET ou POST sans titres : On affiche la Forge (le formulaire)
    media_settings = DIFFICULTY_SETTINGS.get(media_type, DIFFICULTY_SETTINGS["Anime"])
    rank_limit = media_settings.get(difficulty, 300)
    
    # Pool d'items filtrés par difficulté
    full_pool = data.get('db', [])
    if rank_limit is not None:
        if data.get('lookup'):
            limit_titles = [ (t.get('title') or t.get('name')) for t in data['lookup'][:rank_limit] ]
            pool = [item for item in full_pool if (item.get('title') or item.get('name')) in limit_titles]
        else:
            pool = full_pool[:rank_limit]
    else:
        pool = full_pool

    # Sélection des covers d'exemple via le Presenter
    example_covers = ArchetypistPresenter.get_example_covers(pool)
    
    # Construction des items pour la Forge via le Presenter
    display_items = ArchetypistPresenter.build_forge_items(data)

    # On précharge aussi les listes pour les options cross-media
    cross_data = {}
    for opt in cross_options:
        d_opt = animetix_service.load_data(opt['type'])
        if d_opt:
            cross_data[opt['type']] = ArchetypistPresenter.build_forge_items(d_opt, limit=300)

    return render(request, 'animetix/archetypist/archetypist_form.html', {
        'items_json': json.dumps(display_items), 
        'media_type': media_type,
        'example_covers': example_covers,
        'cross_options': cross_options,
        'cross_data_json': json.dumps(cross_data)
    })


def paradox_view(request):
    media_type, data = get_current_mode(request), animetix_service.load_data(get_current_mode(request))
    if not data: return redirect('index')
    is_daily = request.session.get('is_daily', False)
    
    if is_daily and request.session.get('paradox_answer') == request.session.get('secret_title'):
        pass
    else:
        # Préparation via le Domaine
        res_prepare = animetix_service.paradox_service.prepare_challenge(
            data, is_daily, request.session.get('secret_title')
        )
        
        if not res_prepare or len(res_prepare) < 3:
            return redirect('index')
            
        t1, t2, intruder = res_prepare
        
        # Génération du scénario via le Domaine (IA)
        res = animetix_service.paradox_service.generate_logic(
            media_type, 
            data['title_to_full_data'][t1], 
            data['title_to_full_data'][t2], 
            data['title_to_full_data'][intruder], 
            request.session.get('language', 'Français')
        )
        
        request.session.update({
            'paradox_answer': intruder, 
            'paradox_options': [t1, t2, intruder], 
            'paradox_reasoning': res.get('reasoning'), 
            'paradox_scenario': res.get('scenario'), 
            'paradox_media': media_type
        })
        if is_daily: request.session['is_daily'] = True
        
    options = [{'title': t, 'image': data['title_to_full_data'][t].get('image')} for t in request.session.get('paradox_options')]
    random.shuffle(options)
    
    return render(request, 'animetix/paradox/intruder.html', {
        'scenario': request.session.get('paradox_scenario'), 
        'options': options, 
        'media_type': media_type, 
        'is_daily': is_daily
    })

def paradox_guess(request):
    if request.method == 'POST':
        form = GameGuessForm(request.POST)
        if form.is_valid():
            choice = form.cleaned_data['guess']
            answer = request.session.get('paradox_answer', "")
            titles = request.session.get('paradox_options', [])
            media = request.session.get('paradox_media', 'Anime')
            is_daily, is_correct = request.session.get('is_daily', False), (choice == answer)
            data = animetix_service.load_data(media)
            
            if is_correct and request.user.is_authenticated: 
                newly_unlocked = request.user.profile.add_win(
                    is_daily=is_daily,
                    game_mode='paradox',
                    media_type=media,
                    attempts=1
                )
                handle_win_achievements(request, newly_unlocked)
            
            final_opts = [
                {
                    'title': t, 
                    'is_intruder': (t == answer), 
                    'is_user_choice': (t == choice), 
                    'image': data['title_to_full_data'].get(t, {}).get('image') if data else None
                } for t in titles
            ]
            
            return render(request, 'animetix/paradox/intruder_result.html', {
                'is_correct': is_correct, 
                'answer': answer, 
                'reasoning': request.session.get('paradox_reasoning'), 
                'final_options': final_opts, 
                'media_type': media, 
                'is_daily': is_daily
            })
    return redirect('index')

def undercover_party_setup(request): return render(request, 'animetix/undercover/undercover_setup.html', {'media_type': get_current_mode(request)})
def undercover_online_join(request):
    if request.method == 'POST': return redirect('undercover_online_room', room_code=(request.POST.get('room_code', '').upper().strip() or ''.join(random.choices("ABCDE123", k=4))))
    return redirect('undercover_party_setup')
def undercover_online_room(request, room_code): 
    return render(request, 'animetix/undercover/online_room.html', {
        'room_code': room_code,
        'media_type': get_current_mode(request),
        'difficulty': request.session.get('difficulty', 'Normal')
    })
def codemanga_setup(request): return render(request, 'animetix/codemanga/setup.html', {'media_type': get_current_mode(request)})
def codemanga_room(request, room_code): 
    return render(request, 'animetix/codemanga/room.html', {
        'room_code': room_code,
        'difficulty': request.GET.get('difficulty', 'Normal')
    })
def codemanga_game(request, room_code):
    return render(request, 'animetix/codemanga/game.html', {
        'room_code': room_code,
        'difficulty': request.GET.get('difficulty', 'Normal')
    })

def undercover_party_play(request):
    if request.method == 'POST':
        media, num, diff = get_current_mode(request), int(request.POST.get('num_players', 4)), request.session.get('difficulty', 'Normal')
        
        # Initialisation via le domaine
        player_ids = [str(i+1) for i in range(num)]
        game_data = animetix_service.game_service.start_undercover_game(
            media_type=media,
            difficulty=diff,
            player_ids=player_ids,
            rank_limits=DIFFICULTY_SETTINGS
        )
        
        if not game_data:
            return redirect('index')
            
        players = []
        for p_id, assignment in game_data['assignments'].items():
            # Fix: p_id can be 'p1', 'p2' or a session key. Ensure we have an int for the UI or use string.
            try:
                display_id = int(p_id)
            except ValueError:
                # If it's something like 'p1', extract the number
                numeric_part = ''.join(filter(str.isdigit, p_id))
                display_id = int(numeric_part) if numeric_part else random.randint(1, 1000)

            players.append({
                "id": display_id, 
                "role": assignment['role'], 
                "title": assignment['word'], 
                "image": assignment['image']
            })
            
        clue = langchain_service.generate_undercover_clue(media, game_data['civil_word'], game_data['undercover_word'], request.session.get('language', 'Français')) if langchain_service else "..."
        
        return render(request, 'animetix/undercover/undercover_party.html', {
            'num_players': num, 
            'players': players, 
            'clue': clue, 
            'icon': "🦙", 
            'difficulty': diff
        })
    
    return redirect('index')
    
    return redirect('index')

def reveal_hint(request, hint_type):
    revealed = request.session.get('revealed_hints', [])
    if hint_type not in revealed: revealed.append(hint_type); request.session['revealed_hints'] = revealed
    request.session.modified = True
    return redirect('game')

def latent_space_view(request):
    """Affiche la visualisation 3D de l'espace latent des embeddings."""
    media = request.GET.get('media', 'anime').lower()
    vibe_type = request.GET.get('type', 'thematic').lower()
    
    # Mapping des fichiers
    file_map = {
        'anime': {
            'thematic': 'latent_space_anime_thematic.json',
            'visual': 'latent_space_anime_visual_vibe.json',
            'scenario': 'latent_space_anime_plot.json'
        },
        'manga': {
            'thematic': 'latent_space_manga_thematic.json',
            'visual': 'latent_space_manga_visual_vibe.json',
            'scenario': 'latent_space_manga_plot.json'
        },
        'character': {
            'thematic': 'latent_space_character_vibe.json',
            'visual': 'latent_space_character_visual_vibe.json'
        }
    }
    
    filename = file_map.get(media, file_map['anime']).get(vibe_type, 'latent_space_anime_thematic.json')
    
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_file_dir))
    data_path = os.path.join(project_root, 'data', 'artifacts', filename)
    
    # Fallback si le fichier spécifique n'existe pas
    if not os.path.exists(data_path):
        data_path = os.path.join(project_root, 'data', 'artifacts', 'latent_space_3d.json')
    
    latent_data = "[]"
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            latent_data = f.read()
            
    return render(request, 'animetix/mlops/latent_viz.html', {
        'latent_data_json': latent_data,
        'current_media': media,
        'current_type': vibe_type
    })

def submit_ai_feedback(request):
    """Enregistre le feedback utilisateur sur une génération IA via HTMX."""
    if request.method == 'POST':
        is_pos = request.POST.get('is_positive') == 'true'
        f_type = request.POST.get('type', 'general')
        context = request.POST.get('context', '')
        output = request.POST.get('output', '')
        
        from .models import AIFeedback
        AIFeedback.objects.create(
            user=request.user if request.user.is_authenticated else None,
            feedback_type=f_type,
            input_context=context,
            output_text=output,
            is_positive=is_pos
        )
        
        # Retourne un message de remerciement qui remplace les boutons
        return render(request, 'animetix/partials/feedback_thanks.html')
    return redirect('index')

from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User

def global_boss_view(request):
    """Affiche le défi mondial collaboratif."""
    boss = GlobalBoss.objects.filter(is_active=True).first()
    if not boss:
        return redirect('index')
        
    participations = BossParticipation.objects.filter(boss=boss).order_by('-points_contributed')[:10]
    user_participation = None
    if request.user.is_authenticated:
        user_participation = BossParticipation.objects.filter(user=request.user, boss=boss).first()

    hp_percent = 100
    if boss.total_hp > 0:
        hp_percent = (boss.current_hp / boss.total_hp) * 100
    
    return render(request, 'animetix/boss/boss.html', {
        'boss': boss,
        'hp_percent': hp_percent,
        'participations': participations,
        'user_participation': user_participation,
        'txt': animetix_service.translations.get(request.session.get('language', 'Français'), {})
    })

def global_boss_guess(request):
    """Permet à un utilisateur d'attaquer le boss avec phases de combat."""
    if request.method == 'POST' and request.user.is_authenticated:
        form = GameGuessForm(request.POST)
        if form.is_valid():
            guess_title = form.cleaned_data['guess']
            boss = GlobalBoss.objects.filter(is_active=True, current_hp__gt=0).first()
            if not boss: return redirect('global_boss')
            
            data = animetix_service.load_data(boss.media_type)
            if not data: return redirect('global_boss')
                
            raw_sim = animetix_service.game_service.calculate_raw_similarity(
                boss.media_type, boss.secret_title, guess_title, data
            )
            
            # Application des modificateurs de phase
            damage_mult = 1.0
            if boss.current_phase == 2: damage_mult = 0.7 # Berserk: Plus résistant
            elif boss.current_phase == 3: damage_mult = 0.4 # Enraged: Très résistant
            
            damage = int(raw_sim * 100 * damage_mult)
            if guess_title == boss.secret_title:
                damage = boss.current_hp 
            
            boss.current_hp = max(0, boss.current_hp - damage)
            phase_changed = boss.update_phase() # Vérifie si on change de phase (ex: 50% HP)
            boss.save()
            
            part, _ = BossParticipation.objects.get_or_create(user=request.user, boss=boss)
            part.points_contributed += damage
            part.save()
            
            if boss.current_hp <= 0:
                boss.is_active = False; boss.save()
                request.user.profile.xp += boss.reward_xp; request.user.profile.save()
            
            if request.headers.get('HX-Request'):
                return render(request, 'animetix/boss/boss_fragment.html', {
                    'boss': boss, 'damage': damage, 'phase_changed': phase_changed,
                    'hp_percent': (boss.current_hp / boss.total_hp) * 100 if boss.total_hp > 0 else 0
                })
    return redirect('global_boss')

def follow_user(request, user_id):
    """Permet de suivre un autre joueur."""
    if not request.user.is_authenticated: return redirect('login')
    to_user = User.objects.get(id=user_id)
    if to_user != request.user:
        Friendship.objects.get_or_create(from_user=request.user, to_user=to_user)
    return redirect(request.META.get('HTTP_REFERER', 'index'))

def abandon_game(request):
    request.session['game_over'] = True; request.session.modified = True; return redirect('game')

# --- MODE 4 : BLIND TEST ---

def blindtest_view(request):
    media_type = "Anime"
    data = animetix_service.load_data(media_type)
    if not data: return redirect('index')

    is_daily = request.session.get('is_daily', False)
    theme_pref = request.GET.get('type') # 'OP', 'ED' or None (Both)

    if request.GET.get('new') == '1' or 'blindtest_secret' not in request.session or is_daily:
        if is_daily:
            theme = blindtest_service.get_daily_theme(datetime.date.today())
        else:
            theme = blindtest_service.get_random_theme(theme_type=theme_pref)
            
        if not theme: return redirect('index')
        
        request.session.update({
            'blindtest_secret': theme['anime_title'],
            'blindtest_song': theme['song_title'],
            'blindtest_artists': theme['artists'],
            'blindtest_video': theme['video_url'],
            'blindtest_type': theme['type'],
            'blindtest_guesses': [],
            'blindtest_game_over': False
        })
        if is_daily: request.session['is_daily'] = True

    return render(request, 'animetix/blindtest/game.html', {
        'video_url': request.session.get('blindtest_video'),
        'theme_type': request.session.get('blindtest_type'),
        'theme_pref': theme_pref,
        'blindtest_song': request.session.get('blindtest_song'),
        'blindtest_artists': request.session.get('blindtest_artists'),
        'guesses': request.session.get('blindtest_guesses'),
        'game_over': request.session.get('blindtest_game_over'),
        'is_daily': is_daily,
        'secret_title': request.session.get('blindtest_secret') if request.session.get('blindtest_game_over') else None,
        'remaining_items_json': data.get('autocomplete_json', '[]')
    })

def blindtest_guess(request):
    if request.method == 'POST' and not request.session.get('blindtest_game_over'):
        guess_title = request.POST.get('guess')
        secret = request.session.get('blindtest_secret')
        media_type = "Anime"
        data = animetix_service.load_data(media_type)
        is_daily = request.session.get('is_daily', False)
        
        if guess_title:
            # VÉRIFICATION INTELLIGENTE (SMART MATCH)
            secret_item = data['title_to_full_data'].get(secret)
            is_correct = animetix_service.game_service.check_title_match(guess_title, secret_item)
            
            guesses = request.session.get('blindtest_guesses', [])
            guess_full = data['title_to_full_data'].get(guess_title)
            
            if guess_full:
                guesses.append({
                    'title': str(guess_title),
                    'image': str(guess_full.get('image')) if guess_full.get('image') else None,
                    'is_correct': bool(is_correct)
                })
                request.session['blindtest_guesses'] = guesses
                
                if is_correct:
                    request.session['blindtest_game_over'] = True
                    if request.user.is_authenticated:
                        newly_unlocked = request.user.profile.add_win(
                            is_daily=is_daily,
                            game_mode='blindtest',
                            media_type=media_type,
                            attempts=len(request.session.get('blindtest_guesses', []))
                        )
                        handle_win_achievements(request, newly_unlocked)
            request.session.modified = True
            
    return redirect('blindtest')

# --- MODE 5 : COVER TEST ---

def covertest_view(request):
    media_type = "Manga"
    data = animetix_service.load_data(media_type)
    if not data: return redirect('index')

    is_daily = request.session.get('is_daily', False)

    if request.GET.get('new') == '1' or 'covertest_secret' not in request.session or is_daily:
        if is_daily:
            cover = covertest_service.get_daily_cover(datetime.date.today())
        else:
            cover = covertest_service.get_random_cover()
            
        if not cover: return redirect('index')
        
        request.session.update({
            'covertest_secret': cover['manga_title'],
            'covertest_url': cover['cover_url'],
            'covertest_locale': cover['locale'],
            'covertest_volume': cover['volume'],
            'covertest_guesses': [],
            'covertest_game_over': False
        })
        if is_daily: request.session['is_daily'] = True

    return render(request, 'animetix/manga/cover_test.html', {
        'cover_url': request.session.get('covertest_url'),
        'locale': request.session.get('covertest_locale'),
        'volume': request.session.get('covertest_volume'),
        'guesses': request.session.get('covertest_guesses'),
        'game_over': request.session.get('covertest_game_over'),
        'is_daily': is_daily,
        'secret_title': request.session.get('covertest_secret') if request.session.get('covertest_game_over') else None,
        'remaining_items_json': data.get('autocomplete_json', '[]')
    })

def covertest_guess(request):
    if request.method == 'POST' and not request.session.get('covertest_game_over'):
        guess_title = request.POST.get('guess')
        secret = request.session.get('covertest_secret')
        media_type = "Manga"
        data = animetix_service.load_data(media_type)
        is_daily = request.session.get('is_daily', False)
        
        if guess_title:
            # VÉRIFICATION INTELLIGENTE (SMART MATCH)
            secret_item = data['title_to_full_data'].get(secret)
            is_correct = animetix_service.game_service.check_title_match(guess_title, secret_item)
            
            guesses = request.session.get('covertest_guesses', [])
            guess_full = data['title_to_full_data'].get(guess_title)
            
            if guess_full:
                guesses.append({
                    'title': str(guess_title),
                    'image': str(guess_full.get('image')) if guess_full.get('image') else None,
                    'is_correct': bool(is_correct)
                })
                request.session['covertest_guesses'] = guesses
                
                if is_correct:
                    request.session['covertest_game_over'] = True
                    if request.user.is_authenticated:
                        newly_unlocked = request.user.profile.add_win(
                            is_daily=is_daily,
                            game_mode='covertest',
                            media_type=media_type,
                            attempts=len(request.session.get('covertest_guesses', []))
                        )
                        handle_win_achievements(request, newly_unlocked)
            request.session.modified = True
            
    return redirect('covertest')

def health_check_view(request):
    """Dashboard de santé technique."""
    status = animetix_service.get_status()
    return render(request, 'animetix/admin/health.html', {'status': status})

def ai_evaluation_dashboard(request):
    """Dashboard de monitoring de la qualité de l'IA (RAGAS)."""
    from .models import AIREvalResult
    results = AIREvalResult.objects.all().order_by('-created_at')[:50]
    
    # Statistiques globales
    from django.db.models import Avg, Count
    stats = AIREvalResult.objects.aggregate(
        avg_faith=Avg('faithfulness'),
        avg_rel=Avg('relevancy'),
        avg_prec=Avg('precision'),
        total=Count('id')
    )
    
    hallucinations = AIREvalResult.objects.filter(hallucination_detected=True).count()
    
    return render(request, 'animetix/admin/ai_eval.html', {
        'results': results,
        'stats': stats,
        'hallucination_count': hallucinations
    })

# --- SOCIAL & COMMUNITY ---

@login_required
def toggle_follow(request, user_id):
    """Suit ou ne suit plus un utilisateur via AJAX/HTMX."""
    from django.contrib.auth.models import User
    from .models import Friendship
    
    target_user = User.objects.get(id=user_id)
    if target_user == request.user:
        return HttpResponse(status=400)
        
    friendship, created = Friendship.objects.get_or_create(
        from_user=request.user, 
        to_user=target_user
    )
    
    if not created:
        friendship.delete()
        is_following = False
    else:
        is_following = True
        
    if request.headers.get('HX-Request'):
        return render(request, 'animetix/social/follow_button_fragment.html', {
            'target_user': target_user,
            'is_following': is_following
        })
        
    return redirect('profile_view', username=target_user.username)

@login_required
def social_dashboard(request):
    """Affiche la liste des amis et leur activité."""
    following = request.user.following.all().select_related('to_user__profile')
    followers = request.user.followers.all().select_related('from_user__profile')
    
    return render(request, 'animetix/social/dashboard.html', {
        'following': following,
        'followers': followers
    })

from django.http import StreamingHttpResponse
import json

def emoji_decode_stream(request):
    """Streaming de la génération d'emojis avec CoT."""
    media_type = get_current_mode(request)
    data = animetix_service.load_data(media_type)
    secret = request.GET.get('secret')
    
    if not secret: return HttpResponse(status=400)

    def event_stream():
        service = animetix_service.emoji_service
        try:
            for event in service.generate_emojis_stream(media_type, secret, data['title_to_full_data'][secret].get('description', '')):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')

def paradox_stream(request):
    """Streaming du raisonnement paradoxal avec CoT."""
    media_type = get_current_mode(request)
    data = animetix_service.load_data(media_type)
    
    t1, t2, intruder = request.GET.get('t1'), request.GET.get('t2'), request.GET.get('intruder')
    if not all([t1, t2, intruder]): return HttpResponse(status=400)

    def event_stream():
        service = animetix_service.paradox_service
        item_a, item_b, item_i = data['title_to_full_data'][t1], data['title_to_full_data'][t2], data['title_to_full_data'][intruder]
        
        try:
            for event in service.generate_logic_stream(media_type, item_a, item_b, item_i, request.session.get('language', 'Français')):
                # Pour le type 'result', on doit transformer l'objet ParadoxLogic en dict
                if event['type'] == 'result':
                    event['content'] = {
                        'reasoning': event['content'].reasoning,
                        'scenario': event['content'].scenario
                    }
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')

def agentic_rag_stream(request):
    """
    Endpoint SSE pour le streaming de l'Agentic RAG.
    """
    query = request.GET.get('q', '')
    media_type = get_current_mode(request)

    if not query:
        return JsonResponse({'error': 'No query provided'}, status=400)

    def event_stream():
        from .containers import get_container
        # On utilise l'instance centralisée du service agentique
        agent = get_container().agentic_rag
        user_id = str(request.user.id) if request.user.is_authenticated else None

        try:
            for event in agent.plan_and_solve_stream(query, media_type, user_id=user_id):
                # Format SSE: data: <json>\n\n
                yield f"data: {json.dumps(event)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    return response
@csrf_exempt
def sync_offline_data(request):
    """Endpoint pour le Background Sync de la PWA. Reçoit les scores offline et met à jour l'XP."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # data: [{'score': 100, 'game_mode': 'classic', 'media_type': 'Anime', 'timestamp': ...}]
            
            if request.user.is_authenticated:
                xp_gained = 0
                for game in data:
                    if game.get('score', 0) == 100:
                        request.user.profile.add_win(
                            is_daily=False,
                            game_mode=game.get('game_mode', 'classic'),
                            media_type=game.get('media_type', 'Anime'),
                            attempts=game.get('attempts', 1)
                        )
                        xp_gained += 10 # Base XP pour une victoire offline
                        
                if xp_gained > 0:
                    request.user.profile.xp += xp_gained
                    request.user.profile.save()
                    
            return JsonResponse({'status': 'success', 'synced_items': len(data)})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return HttpResponse(status=405)

def profile_view(request, username):

    """Affiche le profil public d'un joueur."""
    from django.contrib.auth.models import User
    from .models import Friendship, UserAchievement
    
    user = User.objects.get(username=username)
    is_following = False
    if request.user.is_authenticated:
        is_following = Friendship.objects.filter(from_user=request.user, to_user=user).exists()
        
    achievements = UserAchievement.objects.filter(user=user).select_related('achievement')
    
    return render(request, 'animetix/social/profile.html', {
        'profile_user': user,
        'is_following': is_following,
        'unlocked_achievements': achievements
    })

# --- DUELS 1VS1 (REAL-TIME) ---

@login_required
def create_duel(request):
    """Crée une salle de duel et redirige l'initiateur."""
    import string
    media_type = get_current_mode(request)
    data = animetix_service.load_data(media_type)
    
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    secret = random.choice(data.get('titles', ['Naruto']))
    
    from .models import DuelRoom
    duel = DuelRoom.objects.create(
        room_code=code,
        player1=request.user,
        media_type=media_type,
        secret_title=secret
    )
    
    return redirect('duel_room', room_code=code)

@login_required
def join_duel(request):
    """Rejoint une salle de duel via un code."""
    if request.method == 'POST':
        code = request.POST.get('room_code', '').upper().strip()
        from .models import DuelRoom
        try:
            duel = DuelRoom.objects.get(room_code=code, is_finished=False)
            if duel.player1 != request.user:
                duel.player2 = request.user
                duel.save()
            return redirect('duel_room', room_code=code)
        except DuelRoom.DoesNotExist:
            return redirect('index')
    return render(request, 'animetix/social/join_duel.html')

@login_required
def finish_duel(request, room_code):
    """Marque un duel comme terminé et déclenche le nettoyage des ressources WebSocket."""
    try:
        duel = DuelRoom.objects.get(room_code=room_code)
        if request.user in [duel.player1, duel.player2]:
            duel.is_finished = True
            duel.save()
            
            from .tasks import cleanup_duel_resources_task
            cleanup_duel_resources_task.delay(room_code)
            
            return JsonResponse({'status': 'duel_finished'})
    except DuelRoom.DoesNotExist:
        pass
    return redirect('index')

@login_required
def duel_room_view(request, room_code):
    """Affiche la salle de duel (UI WebSocket)."""
    from .models import DuelRoom
    try:
        duel = DuelRoom.objects.get(room_code=room_code)
        return render(request, 'animetix/social/duel_room.html', {
            'duel': duel,
            'is_p1': duel.player1 == request.user
        })
    except DuelRoom.DoesNotExist:
        return redirect('index')

# --- MLOPS : DATA CURATION ---

@staff_member_required
def gold_curation_view(request):
    """Interface d'administration pour valider les données de Fine-Tuning."""
    from .models import GoldDatasetEntry, AIFeedback
    
    # On importe automatiquement les nouveaux feedbacks positifs qui n'ont pas encore d'entrée Gold
    positive_feedbacks = AIFeedback.objects.filter(is_positive=True).exclude(golddatasetentry__isnull=False)
    for fb in positive_feedbacks:
        GoldDatasetEntry.objects.create(
            context=fb.input_context,
            instruction="Réponds à la question de l'utilisateur sur l'anime/manga.",
            response=fb.output_text,
            source_feedback=fb
        )
        
    entries = GoldDatasetEntry.objects.filter(is_validated=False).order_by('-created_at')
    validated_count = GoldDatasetEntry.objects.filter(is_validated=True).count()
    
    return render(request, 'animetix/admin/gold_curation.html', {
        'entries': entries,
        'validated_count': validated_count
    })

@staff_member_required
def validate_gold_entry(request, entry_id):
    from .models import GoldDatasetEntry
    try:
        entry = GoldDatasetEntry.objects.get(id=entry_id)
        entry.is_validated = True
        entry.save()
        return HttpResponse(status=204)
    except GoldDatasetEntry.DoesNotExist:
        return HttpResponse(status=404)

@staff_member_required
def reject_gold_entry(request, entry_id):
    from .models import GoldDatasetEntry
    try:
        GoldDatasetEntry.objects.get(id=entry_id).delete()
        return HttpResponse(status=204)
    except GoldDatasetEntry.DoesNotExist:
        return HttpResponse(status=404)
