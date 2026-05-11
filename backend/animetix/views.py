from django.shortcuts import render, redirect
from django.http import JsonResponse
from .services import AnimetixService, LangChainService, BlindTestService, CoverTestService, check_achievements, DIFFICULTY_SETTINGS
from .models import Profile, DailyChallenge, ChallengeResult, Achievement, UserAchievement, GameplaySession
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

# Initialize services
animetix_service = AnimetixService()
blindtest_service = BlindTestService()
covertest_service = CoverTestService()

try:
    langchain_service = LangChainService()
except Exception as e:
    print(f"Warning: LangChainService could not be initialized: {e}")
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
    try:
        coll_name = f"{mode.lower()}_thematic"
        if mode == 'Character': coll_name = "character_vibe"
        collection = animetix_service.get_chroma_collection(coll_name)
        res = collection.get(ids=[str(data['title_to_full_data'][secret_title]['id']), 
                                  str(data['title_to_full_data'][guess_title]['id'])], 
                             include=['embeddings'])
        if len(res['embeddings']) == 2:
            vec1 = np.array(res['embeddings'][0]).reshape(1, -1)
            vec2 = np.array(res['embeddings'][1]).reshape(1, -1)
            return float(cosine_similarity(vec1, vec2)[0][0])
    except Exception as e:
        print(f"Chroma Similarity Error: {e}")
    return 0.0

def calculate_raw_similarity(media_type, secret_title, guess_title, data):
    if secret_title == guess_title: return 1.0
    secret_full, guess_full = data['title_to_full_data'][secret_title], data['title_to_full_data'][guess_title]
    vec_sim = get_similarity_score(media_type, secret_title, guess_title, data)
    if media_type == 'Character':
        org_S = set(secret_full.get('metadata', {}).get('affiliations', []))
        org_G = set(guess_full.get('metadata', {}).get('affiliations', []))
        org_sim = 1.0 if len(org_S.intersection(org_G)) > 0 else 0.0
        return (0.7 * vec_sim) + (0.3 * org_sim)
    else: return vec_sim

# --- VIEWS ---

def index(request):
    mode = get_current_mode(request)
    profile = request.user.profile if request.user.is_authenticated else None
    
    # Sélection aléatoire de l'image de héros
    home_images = ["Dio.png", "Gintama.png", "Mugiwara.png", "Team_7.png", "Z_team.png"]
    random_hero = random.choice(home_images)

    # Définition des modes de jeu avec style "Character Card"
    modes_solo = [
        {
            "titre": "Classic Mode",
            "titre_brush_1": "CLASSIC",
            "titre_brush_2": "MODE",
            "description": "Trouvez le titre mystère grâce à la similarité sémantique.",
            "url": "start_game",
            "icon_url": "/static/animetix/img/ui/frieren.png",
            "gradient": "from-blue-600 via-indigo-500 to-blue-400", # Vibrant Blue
            "post_only": True
        },
        {
            "titre": "Emoji Decode",
            "titre_brush_1": "EMOJI",
            "titre_brush_2": "DECODE",
            "description": "Déchiffrez les symboles pour identifier l'œuvre cachée.",
            "url": "emoji_decode",
            "icon_url": "/static/animetix/img/ui/Shaman_king.png",
            "gradient": "from-orange-600 via-red-500 to-amber-400", # Vibrant Orange/Red
            "post_only": False
        },
        {
            "titre": "Animinator Oracle",
            "titre_brush_1": "ANIMINATOR",
            "titre_brush_2": "ORACLE",
            "description": "Posez vos questions à l'Oracle pour débusquer le secret.",
            "url": "animinator",
            "icon_url": "/static/animetix/img/ui/Sinbad.png",
            "gradient": "from-purple-700 via-violet-600 to-purple-400", # Deep Purple
            "post_only": False
        },
        {
            "titre": "Akinetix Devin",
            "titre_brush_1": "AKINETIX",
            "titre_brush_2": "DEVIN",
            "description": "L'IA analyse vos pensées pour deviner ce que vous cachez.",
            "url": "akinetix",
            "icon_url": "/static/animetix/img/ui/Saiki.png",
            "gradient": "from-pink-600 via-rose-500 to-pink-400", # Vibrant Pink
            "post_only": False
        },
        {
            "titre": "Paradox Quest",
            "titre_brush_1": "PARADOX",
            "titre_brush_2": "QUEST",
            "description": "Débusquez l'intrus parmi les scénarios générés par l'IA.",
            "url": "paradox",
            "icon_url": "/static/animetix/img/ui/Steins_gate.png",
            "gradient": "from-red-700 via-rose-600 to-red-400", # Intense Red
            "post_only": True
        },
        {
            "titre": "Vision Quest",
            "titre_brush_1": "VISION",
            "titre_brush_2": "QUEST",
            "description": "Défiez la reconnaissance visuelle de l'IA en décrivant l'image.",
            "url": "vision_quest",
            "icon_url": "/static/animetix/img/ui/SAO.png",
            "gradient": "from-cyan-600 via-blue-500 to-sky-400", # Deep Cyan/Blue
            "post_only": False
        },
        {
            "titre": "Blind Test",
            "titre_brush_1": "BLIND",
            "titre_brush_2": "TEST",
            "description": "Devinez l'animé à partir de son opening ou ending.",
            "url": "blindtest",
            "icon_url": "/static/animetix/img/ui/Kaori.png",
            "gradient": "from-green-600 via-teal-500 to-emerald-400", # Vibrant Green/Teal
            "post_only": True
        },
        {
            "titre": "Cover Test",
            "titre_brush_1": "COVER",
            "titre_brush_2": "TEST",
            "description": "Devinez le manga à partir de sa couverture (JA/FR).",
            "url": "covertest",
            "icon_url": "/static/animetix/img/ui/Bakuman.png",
            "gradient": "from-amber-600 via-yellow-500 to-orange-400", # Vibrant Amber/Orange
            "post_only": True
        },
    ]
    
    modes_multi = [
        {"titre": "Undercover", "description": "Débusquez l'intrus.", "url": "undercover_party_setup", "icon_url": "/static/animetix/img/ui/Light.png", "is_new": False, "post_only": False},
        {"titre": "Code Manga", "description": "Agents secrets.", "url": "codemanga", "icon_url": "/static/animetix/img/ui/code_manga.png", "is_new": False, "post_only": False},
    ]
    
    modes_creative = [
        {
            "titre": "Fusion d'Univers",
            "titre_sub": "CRÉEZ DES MONDES UNIQUES À TOUT MOMENT",
            "url": "archetypist",
            "fusion_image": "/static/animetix/img/ui/Fusion.png",
            "post_only": False
        },
    ]
    
    media_collections = [
        {"nom": "ANIME", "mode": "Anime", "image": "/static/animetix/img/anime.png"},
        {"nom": "MANGA", "mode": "Manga", "image": "/static/animetix/img/manga.png"},
        {"nom": "PERSO", "mode": "Character", "image": "/static/animetix/img/perso.png"},
    ]

    context = {
        'current_mode': mode,
        'profile': profile,
        'modes_solo': modes_solo,
        'modes_multi': modes_multi,
        'modes_creative': modes_creative,
        'media_collections': media_collections,
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
            mode = request.session.get('custom_mode', 'all')
            whitelist = request.session.get('custom_whitelist', [])
            blacklist = request.session.get('custom_blacklist', [])
            g_white = request.session.get('custom_genres_white', [])
            g_black = request.session.get('custom_genres_black', [])
            t_white = request.session.get('custom_tags_white', [])
            t_black = request.session.get('custom_tags_black', [])
            
            # 1. Base Pool
            if mode == 'white' and whitelist:
                pool = [data['title_to_full_data'][t] for t in whitelist if t in data['title_to_full_data']]
            else:
                pool = [item for item in data['db'] if (item.get('title') or item.get('name')) not in blacklist]
            
            # 2. Filtrage par Genres/Tags
            filtered_pool = []
            for item in pool:
                item_genres = set(item.get('genres', []))
                item_tags = set(item.get('tags', []))
                
                # Règle d'exclusion (Blacklist)
                if any(g in item_genres for g in g_black) or any(t in item_tags for t in t_black):
                    continue
                
                # Règle d'inclusion (Whitelist) - Doit avoir au moins un des genres/tags demandés
                if g_white or t_white:
                    if not (any(g in item_genres for g in g_white) or any(t in item_tags for t in t_white)):
                        continue
                
                filtered_pool.append(item)
            
            if not filtered_pool: filtered_pool = data['db'][:50] # Fallback
            if not filtered_pool: return redirect('index')
            secret_obj = random.choice(filtered_pool)
            secret_title = secret_obj.get('title') or secret_obj.get('name')
        else:
            # Sélection classique
            media_settings = DIFFICULTY_SETTINGS.get(media_type, DIFFICULTY_SETTINGS["Anime"])
            rank_limit = media_settings.get(difficulty, 300)
            valid_titles = [item.get('title') or item.get('name') for item in data.get("lookup", [])[:rank_limit] if (item.get('title') or item.get('name')) in data.get('title_to_full_data', {})]
            if not valid_titles: valid_titles = data.get('titles', [])[:50]
            if not valid_titles: return redirect('index')
            secret_title = random.choice(valid_titles)

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

def game_view(request):
    media_type = request.session.get('media_type', 'Anime'); data = animetix_service.load_data(media_type)
    if not data or 'secret_title' not in request.session: return redirect('index')
    guessed_titles = [g['title'] for g in request.session.get('guesses', [])]
    secret_title = request.session.get('secret_title'); secret_data = data['title_to_full_data'].get(secret_title)
    if not secret_data: return redirect('index')
    hints = {k: {'revealed': k in request.session.get('revealed_hints', []), 'locked': True} for k in ['poster', 'character', 'culture', 'rec', 'sim', 'chars', 'origin', 'words', 'vibe']}
    hints['poster'] = {'revealed': 'poster' in request.session.get('revealed_hints', []), 'value': secret_data.get('image'), 'locked': False}
    return render(request, 'animetix/classic/game.html', {
        'media_type': media_type, 'guesses': request.session.get('guesses', []), 'game_over': request.session.get('game_over', False),
        'guess_count': len(guessed_titles), 'hints': hints, 'radar_data': json.dumps([]), 
        'is_daily': request.session.get('is_daily', False), 'is_ranked': request.session.get('is_ranked', False),
        'ranked_points': request.user.profile.ranked_points if request.user.is_authenticated else 0,
        'secret_title': secret_title if request.session.get('game_over') else None, 'secret_data': secret_data if request.session.get('game_over') else None,
        'remaining_items': [item for item in data['lookup'] if item['title'] in data['title_to_full_data']]
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
            valid_items = [item for item in data['db'] if item.get('image')]
            secret = random.choice(valid_items[:300])
        
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

def vision_quest_guess(request):
    if request.method == 'POST' and not request.session.get('vision_game_over'):
        query = request.POST.get('description', '').strip()
        secret_id = request.session.get('vision_secret_id')
        secret_title = request.session.get('vision_secret_title')
        media_type = request.session.get('vision_media_type', 'Anime')

        if query:
            # 1. Calcul de similarité visuelle via CLIP
            score = langchain_service.calculate_visual_similarity(query, secret_id, media_type)
            
            # 2. On vérifie si l'utilisateur a carrément deviné le titre (Bonus)
            is_perfect = (query.lower() in secret_title.lower() and score > 85)
            if is_perfect: score = 100.0

            guesses = request.session.get('vision_guesses', [])
            guesses.insert(0, {'text': query, 'score': score})
            request.session['vision_guesses'] = guesses
            
            if score > request.session.get('vision_best_score', 0):
                request.session['vision_best_score'] = score
            
            if score >= 95: # Seuil de victoire
                request.session['vision_game_over'] = True
                if request.user.is_authenticated:
                    request.user.profile.add_win(is_daily=is_daily)
                
                # Enregistrement Session
                GameplaySession.objects.create(
                    game_mode='vision_quest',
                    media_type=media_type,
                    target_item=secret_title,
                    history=guesses,
                    was_won=True
                )
            
            request.session.modified = True
            
    return redirect('vision_quest')

def make_guess(request):
    if request.method == 'POST' and not request.session.get('game_over'):
        guess_title, media_type = request.POST.get('guess'), get_current_mode(request)
        secret_title, max_sim = request.session.get('secret_title'), request.session.get('max_raw_sim', 1.0)
        data = animetix_service.load_data(media_type)
        if not guess_title or guess_title not in data['title_to_index']: return redirect('game')
        raw_sim = calculate_raw_similarity(media_type, secret_title, guess_title, data)
        score = 100.0 if guess_title == secret_title else round(min(0.99, (raw_sim / max_sim) * 0.99) * 100, 2)
        color = "danger" if score > 90 else "warning" if score > 70 else "primary" if score > 40 else "secondary"
        guesses = request.session.get('guesses', []); g_data = data['title_to_full_data'].get(guess_title, {})
        guesses.append({"title": guess_title, "title_english": g_data.get('title_english'), "title_native": g_data.get('title_native'), "image": g_data.get('image'), "score": score, "color": color})
        guesses.sort(key=lambda x: x['score'], reverse=True); request.session['guesses'] = guesses
        if guess_title == secret_title:
            request.session['game_over'] = True
            if request.user.is_authenticated:
                # Trouver le rang de l'item secret pour le calcul des points
                item_rank = 100
                for i, item in enumerate(data['lookup']):
                    if (item.get('title') or item.get('name')) == secret_title:
                        item_rank = i + 1; break
                request.user.profile.add_win(is_daily=request.session.get('is_daily', False), is_ranked=request.session.get('is_ranked', False), item_rank=item_rank)
        request.session.modified = True
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
            valid_choices = [t for t in data['titles'] if t in data['title_to_full_data']][:500]
            if not valid_choices: return redirect('index')
            secret = random.choice(valid_choices)
            
        request.session.update({
            'emoji_secret': secret, 
            'emoji_list': langchain_service.generate_emojis(media_type, secret, data['title_to_full_data'][secret].get('description', '')) if langchain_service else "❓❓❓", 
            'emoji_guesses': [], 
            'emoji_game_over': False
        })
        # On maintient l'état daily/ranked si besoin
        if is_daily: request.session['is_daily'] = True
        if is_ranked: request.session['is_ranked'] = True
    
    # On passe les infos complètes pour l'autocomplétion
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
        guess_title, secret, media_type = request.POST.get('guess'), request.session.get('emoji_secret'), get_current_mode(request)
        data = animetix_service.load_data(media_type)
        guesses = request.session.get('emoji_guesses', [])
        
        # Récupération des infos complètes du guess
        guess_full = data['title_to_full_data'].get(guess_title)
        if guess_full:
            is_correct = (guess_title == secret)
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
                    request.user.profile.add_win(is_daily=request.session.get('is_daily', False), is_ranked=request.session.get('is_ranked', False), item_rank=item_rank)
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
            secret = random.choice([t for t in data['titles'] if t in data['title_to_full_data']][:300])
            
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

def animinator_ask(request):
    if request.method == 'POST' and not request.session.get('animinator_game_over'):
        question = request.POST.get('question'); media_type, data = get_current_mode(request), animetix_service.load_data(get_current_mode(request))
        secret = request.session.get('animinator_secret'); answer = langchain_service.ask_oracle(media_type, secret, data['title_to_full_data'][secret], question) if langchain_service else "???"
        chat = request.session.get('animinator_chat', []); chat.append({'q': question, 'a': answer}); request.session['animinator_chat'] = chat
        q_left = request.session.get('animinator_questions_left', 20) - 1; request.session['animinator_questions_left'] = q_left
        
        if q_left <= 0:
            request.session['animinator_game_over'] = True
            # Save session if lost by running out of questions
            GameplaySession.objects.create(
                game_mode='animinator',
                media_type=media_type,
                target_item=secret,
                history=chat,
                was_won=False
            )
        request.session.modified = True
    return redirect('animinator')

def animinator_guess(request):
    if request.method == 'POST' and not request.session.get('animinator_game_over'):
        guess, secret = request.POST.get('guess'), request.session.get('animinator_secret')
        media_type = get_current_mode(request)
        is_correct = (guess == secret)
        if is_correct:
            request.session['animinator_game_over'] = True
            if request.user.is_authenticated: request.user.profile.add_win(is_daily=request.session.get('is_daily', False))
            
            # Save successful session
            GameplaySession.objects.create(
                game_mode='animinator',
                media_type=media_type,
                target_item=secret,
                history=request.session.get('animinator_chat', []),
                was_won=True
            )
        request.session.modified = True
    return redirect('animinator')

def akinetix_view(request):
    media_type, data = get_current_mode(request), animetix_service.load_data(get_current_mode(request))
    if not data: return redirect('index')
    
    if request.GET.get('new') == '1': request.session['is_daily'] = False
    is_daily = request.session.get('is_daily', False)
    
    if 'akinetix_candidates' not in request.session or request.GET.get('new') == '1' or is_daily:
        # En mode Daily, on cible un item précis (celui du jour)
        if is_daily:
            secret = request.session.get('secret_title')
            candidates = [secret] # Pour Akinetix, on peut restreindre ou non, mais ici on garde la logique de devinette
        else:
            candidates = [t for t in data['titles'] if t in data['title_to_full_data']][:200]
            
        request.session.update({
            'akinetix_candidates': candidates, 
            'akinetix_history': [], 
            'akinetix_current_q': "Es-tu prêt ? Pense à une œuvre et je vais tenter de la deviner.", 
            'akinetix_game_over': False, 
            'akinetix_ai_guess': None
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
        answer, media_type = request.POST.get('answer'), get_current_mode(request); data = animetix_service.load_data(media_type)
        history, curr_q = request.session.get('akinetix_history', []), request.session.get('akinetix_current_q')
        history.append({'q': curr_q, 'a': answer}); request.session['akinetix_history'] = history
        candidates = request.session.get('akinetix_candidates'); res = langchain_service.propose_next_question(media_type, history, candidates)
        if res.startswith('GUESS:'):
            guess_title = res.replace('GUESS:', '').strip()
            request.session.update({'akinetix_current_q': f"Est-ce que tu penses à : {guess_title} ?", 'akinetix_ai_guess': guess_title, 'akinetix_game_over': True})
        else: request.session['akinetix_current_q'] = res
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
            request.user.profile.add_win(is_daily=is_daily)

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
        print(f"⚠️ Celery Result Backend Error: {e}")
        return HttpResponse(status=204) # Ne rien changer si erreur backend
    
    # 204 No Content : Indique à HTMX de ne PAS faire le swap (garde le loader)
    return HttpResponse(status=204)

def archetypist_view(request):
    media_type = get_current_mode(request)
    difficulty = request.session.get('difficulty', 'Normal')
    data = animetix_service.load_data(media_type)
    
    if not data:
        print(f"❌ Archetypist Error: Data for {media_type} not loaded")
        return redirect('index')

    # Définition des options de mélange (cross-media)
    cross_options = []
    if media_type == 'Anime':
        cross_options = [
            {'label': 'Jeux Vidéo', 'type': 'Game', 'icon': 'bi-controller'},
            {'label': 'Mangas', 'type': 'Manga', 'icon': 'bi-book'},
            {'label': 'Films', 'type': 'Movie', 'icon': 'bi-film'},
        ]
    elif media_type == 'Manga':
        cross_options = [
            {'label': 'Jeux Vidéo', 'type': 'Game', 'icon': 'bi-controller'},
            {'label': 'Animes', 'type': 'Anime', 'icon': 'bi-tv'},
            {'label': 'Films', 'type': 'Movie', 'icon': 'bi-film'},
        ]
    elif media_type == 'Character':
        cross_options = [
            {'label': 'Acteurs', 'type': 'Actor', 'icon': 'bi-person-badge'},
            {'label': 'Perso Film', 'type': 'Movie', 'icon': 'bi-film'},
            {'label': 'Perso Jeux', 'type': 'Game', 'icon': 'bi-controller'},
        ]

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
        
        # --- LANCEMENT ASYNC CELERY ---
        from .tasks import generate_full_fusion_task
        task = generate_full_fusion_task.delay(media_type, item1, item2, request.session.get('language', 'Français'))
        
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

    items_with_img = [item for item in pool if item.get('image')]
    if len(items_with_img) < 8: items_with_img = [item for item in full_pool if item.get('image')]
    
    example_covers = random.sample(items_with_img, min(len(items_with_img), 8))
    
    positions = [
        {"style": "top-[-20px] left-[10%] rotate-[-12deg]", "fly": "fly-top"},
        {"style": "top-[20%] left-[-40px] rotate-[8deg]", "fly": "fly-left"},
        {"style": "bottom-[15%] left-[2%] rotate-[-6deg]", "fly": "fly-left"},
        {"style": "bottom-[-50px] left-[30%] rotate-[15deg]", "fly": "fly-bottom"},
        {"style": "bottom-[5%] right-[25%] rotate-[-10deg]", "fly": "fly-bottom"},
        {"style": "top-[10%] right-[-20px] rotate-[-5deg]", "fly": "fly-right"},
        {"style": "bottom-[25%] right-[-30px] rotate-[12deg]", "fly": "fly-right"},
        {"style": "top-[-40px] right-[20%] rotate-[8deg]", "fly": "fly-top"}
    ]
    
    for i, item in enumerate(example_covers):
        pos = positions[i] if i < len(positions) else {"style": "", "fly": "fly-bottom"}
        item['css_style'] = pos["style"]
        item['fly_class'] = pos["fly"]
        item['animation_delay'] = round((i + 1) * 0.15, 2)

    # Helper pour construire une liste propre pour le JS (utilisé par la Forge)
    def build_forge_items(data_dict, limit=500):
        items = []
        # On tente de prendre dans lookup (Chroma) ou db (JSON)
        pool = data_dict.get('lookup', []) if data_dict.get('lookup') else [{"title": t} for t in data_dict.get('titles', [])]
        
        for it in pool:
            title = it.get('title') or it.get('name')
            if not title: continue
            full = data_dict.get('title_to_full_data', {}).get(title, {})
            # Priorité absolue à l'image
            img = it.get('image') or full.get('image')
            if not img: continue # On veut des images dans la Forge !
            
            items.append({
                "title": title,
                "title_native": it.get('title_native') or full.get('title_native') or full.get('title_jp') or "",
                "image": img
            })
            if len(items) >= limit: break
        
        # Fallback si vraiment peu d'images trouvées
        if len(items) < 10:
            for it in pool[:limit]:
                title = it.get('title') or it.get('name')
                if not title: continue
                if any(x['title'] == title for x in items): continue
                full = data_dict.get('title_to_full_data', {}).get(title, {})
                items.append({
                    "title": title,
                    "title_native": it.get('title_native') or full.get('title_native') or full.get('title_jp') or "",
                    "image": it.get('image') or full.get('image') or ""
                })
                if len(items) >= limit: break
        return items

    display_items = build_forge_items(data)

    # On précharge aussi les listes pour les options cross-media
    cross_data = {}
    for opt in cross_options:
        d_opt = animetix_service.load_data(opt['type'])
        if d_opt:
            cross_data[opt['type']] = build_forge_items(d_opt, limit=300)

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
    if is_daily and request.session.get('paradox_answer') == request.session.get('secret_title'): pass
    else:
        valid = [t for t in data['titles'] if t in data['title_to_full_data']]
        if is_daily: intruder, (t1, t2) = request.session.get('secret_title'), random.choices(valid[:100], k=2)
        else: t1, t2, intruder = random.choices(valid[:200], k=2) + [random.choice(valid[500:1000])]
        res = langchain_service.generate_paradox_logic(media_type, data['title_to_full_data'][t1], data['title_to_full_data'][t2], data['title_to_full_data'][intruder], request.session.get('language', 'Français')) if langchain_service else {"scenario": "?"}
        request.session.update({'paradox_answer': intruder, 'paradox_options': [t1, t2, intruder], 'paradox_reasoning': res.get('reasoning'), 'paradox_scenario': res.get('scenario'), 'paradox_media': media_type})
        if is_daily: request.session['is_daily'] = True
    options = [{'title': t, 'image': data['title_to_full_data'][t].get('image')} for t in request.session.get('paradox_options')]; random.shuffle(options)
    return render(request, 'animetix/paradox/intruder.html', {'scenario': request.session.get('paradox_scenario'), 'options': options, 'media_type': media_type, 'is_daily': is_daily})

def paradox_guess(request):
    if request.method == 'POST':
        choice, answer, titles, media = request.POST.get('choice'), request.session.get('paradox_answer'), request.session.get('paradox_options'), request.session.get('paradox_media')
        is_daily, is_correct = request.session.get('is_daily', False), (choice == answer)
        if is_correct and request.user.is_authenticated: request.user.profile.add_win(is_daily=is_daily); data = animetix_service.load_data(media)
        final_opts = [{'title': t, 'is_intruder': (t == answer), 'is_user_choice': (t == choice), 'image': data['title_to_full_data'][t].get('image')} for t in titles]
        return render(request, 'animetix/paradox/intruder_result.html', {'is_correct': is_correct, 'answer': answer, 'reasoning': request.session.get('paradox_reasoning'), 'final_options': final_opts, 'media_type': media, 'is_daily': is_daily})
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
        data = animetix_service.load_data(media)
        
        if not data or 'db' not in data or not data['db']:
            print(f"❌ Undercover Error: Data for {media} is empty or missing 'db'")
            return redirect('index')
        
        # Application de la difficulté
        media_settings = DIFFICULTY_SETTINGS.get(media, DIFFICULTY_SETTINGS["Anime"])
        rank_limit = media_settings.get(diff, 300)
        
        # Construction de la liste des titres valides
        # On privilégie 'lookup' s'il n'est pas vide (car il contient les items présents dans Chroma)
        if data.get('lookup'):
            valid = [ (t.get('title') or t.get('name')) for t in data['lookup'] if (t.get('title') or t.get('name')) in data['title_to_full_data']]
        else:
            # Fallback sur la base complète si Chroma est vide (ex: Characters)
            valid = [ (item.get('title') or item.get('name')) for item in data['db'] ]
            
        if rank_limit is not None:
            valid = valid[:rank_limit]
            
        if not valid:
            print(f"❌ Undercover Error: No valid titles for {media} (diff: {diff}, total_db: {len(data['db'])})")
            return redirect('index')
        
        civil_label = random.choice(valid)
        civil_item = data['title_to_full_data'].get(civil_label)
        if not civil_item:
            print(f"❌ Undercover Error: Selected title {civil_label} not found in title_to_full_data")
            return redirect('index')
            
        civil_id = civil_item['id']
        coll_name = "character_vibe" if media == 'Character' else f"{media.lower()}_thematic"
        
        undercover_label = None
        # On tente de trouver un voisin sémantique seulement si la collection n'est pas vide
        try:
            count = 0
            try:
                coll = animetix_service.get_chroma_collection(coll_name)
                count = coll.count()
            except: pass
            
            if count > 0:
                results = animetix_service.get_nearest_neighbors(coll_name, civil_id, n_results=5)
                if results is not None and results.get('metadatas') and len(results['metadatas'][0]) > 1:
                    candidates = [(m.get('title') or m.get('name')) for m in results['metadatas'][0] if str(m['id']) != str(civil_id)]
                    if candidates: undercover_label = random.choice(candidates)
        except Exception as e:
            print(f"⚠️ Undercover Warning: Chroma neighbor search failed: {e}")

        # Fallback si pas de voisin trouvé (ou collection vide)
        if not undercover_label: 
            print(f"⚠️ Undercover Warning: No neighbors found for {civil_label}, picking random fallback")
            und_valid = [t for t in valid if t != civil_label]
            if not und_valid: 
                # Cas extrême: un seul titre dans toute la base
                undercover_label = civil_label
            else:
                undercover_label = random.choice(und_valid)
            
        players = []; und_pos = random.randint(0, num-1)
        for i in range(num):
            role = "Undercover" if i == und_pos else "Civil"
            target_label = undercover_label if role == "Undercover" else civil_label
            obj = data['title_to_full_data'].get(target_label) or {"title": target_label}
                
            players.append({
                "id": i+1, 
                "role": role, 
                "title": obj.get('title') or obj.get('name'), 
                "title_en": obj.get('title_english') or obj.get('title_en'),
                "title_nat": obj.get('title_native') or obj.get('title_jp'),
                "image": obj.get('image')
            })
            
        clue = langchain_service.generate_undercover_clue(media, civil_label, undercover_label, request.session.get('language', 'Français')) if langchain_service else "..."
        return render(request, 'animetix/undercover/undercover_party.html', {
            'num_players': num, 
            'players': players, 
            'clue': clue, 
            'icon': "🦙", 
            'difficulty': diff
        })
    
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
        
        if guess_title and guess_title in data['title_to_full_data']:
            is_correct = (guess_title == secret)
            guesses = request.session.get('blindtest_guesses', [])
            guess_full = data['title_to_full_data'].get(guess_title)
            
            guesses.append({
                'title': guess_title,
                'image': guess_full.get('image'),
                'is_correct': is_correct
            })
            request.session['blindtest_guesses'] = guesses
            
            if is_correct:
                request.session['blindtest_game_over'] = True
                if request.user.is_authenticated:
                    request.user.profile.add_win(is_daily=is_daily)
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
        
        if guess_title and guess_title in data['title_to_full_data']:
            is_correct = (guess_title == secret)
            guesses = request.session.get('covertest_guesses', [])
            guess_full = data['title_to_full_data'].get(guess_title)
            
            guesses.append({
                'title': guess_title,
                'image': guess_full.get('image'),
                'is_correct': is_correct
            })
            request.session['covertest_guesses'] = guesses
            
            if is_correct:
                request.session['covertest_game_over'] = True
                if request.user.is_authenticated:
                    request.user.profile.add_win(is_daily=is_daily)
            request.session.modified = True
            
    return redirect('covertest')
