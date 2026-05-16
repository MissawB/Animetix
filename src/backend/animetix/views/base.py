import random
import datetime
import hashlib
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse
from .common import animetix_service, logger
from .classic import start_game
from ..utils import get_current_mode, switch_mode, switch_language, switch_difficulty
from ..presenters import ArchetypistPresenter
from ..models import DailyChallenge, ChallengeResult

def index(request):
    mode = get_current_mode(request)
    profile = request.user.profile if request.user.is_authenticated else None
    home_images = ["Dio.png", "Gintama.png", "Mugiwara.png", "Team_7.png", "Z_team.png"]
    random_hero = random.choice(home_images)
    config = ArchetypistPresenter.get_game_modes(getattr(settings, 'FEATURE_FLAGS', {}))
    context = {'current_mode': mode, 'profile': profile, 'modes_solo': config['solo'], 'modes_multi': config['multi'], 'modes_creative': config['creative'], 'media_collections': config['collections'], 'hero_image': random_hero}
    return render(request, 'animetix/index.html', context)


def start_daily_challenge(request):
    media_type, today = get_current_mode(request), datetime.date.today()
    daily, created = DailyChallenge.objects.get_or_create(date=today, defaults={'media_type': media_type, 'secret_title': '', 'game_mode': 'classic'})
    data = animetix_service.load_data(media_type)
    if not data: return redirect('index')
    if created or not daily.secret_title:
        seed = int(hashlib.md5(f"{today}{media_type}".encode()).hexdigest(), 16)
        random.seed(seed); modes = ['classic', 'emoji', 'animinator', 'akinetix', 'paradox', 'vision_quest', 'blindtest', 'covertest']
        daily.game_mode = random.choice(modes); valid_titles = [item.get('title') or item.get('name') for item in data['db']]
        if not valid_titles: return redirect('index')
        daily.secret_title = random.choice(valid_titles[:500]); daily.save(); random.seed(None)
    request.session.update({'is_daily': True, 'daily_id': daily.id, 'secret_title': daily.secret_title, 'media_type': media_type, 'game_over': False})
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
    completed = ChallengeResult.objects.filter(user=request.user, challenge=daily).exists() if request.user.is_authenticated else False
    modes_daily = [{"id": "classic", "brush1": "CLASSIC", "brush2": "MODE", "description": "Trouvez le titre mystère du jour via la similarité.", "icon": "/static/animetix/img/ui/frieren.png", "gradient": "from-blue-600 via-indigo-500 to-blue-400", "completed": completed}, {"id": "emoji", "brush1": "EMOJI", "brush2": "DECODE", "description": "Déchiffrez l'œuvre derrière les emojis du jour.", "icon": "/static/animetix/img/ui/Shaman_king.png", "gradient": "from-orange-600 via-red-500 to-amber-400", "completed": completed}, {"id": "animinator", "brush1": "ANIMINATOR", "brush2": "ORACLE", "description": "Posez vos questions à l'Oracle pour débusquer le secret.", "icon": "/static/animetix/img/ui/Sinbad.png", "gradient": "from-purple-700 via-violet-600 to-purple-400", "completed": completed}, {"id": "akinetix", "brush1": "AKINETIX", "brush2": "DEVIN", "description": "L'IA tente de deviner à quelle œuvre du jour vous pensez.", "icon": "/static/animetix/img/ui/Saiki.png", "gradient": "from-pink-600 via-rose-500 to-pink-400", "completed": completed}, {"id": "paradox", "brush1": "PARADOX", "brush2": "QUEST", "description": "Débusquez l'intrus parmi les propositions du jour.", "icon": "/static/animetix/img/ui/Steins_gate.png", "gradient": "from-red-700 via-rose-600 to-red-400", "completed": completed}, {"id": "vision_quest", "brush1": "VISION", "brush2": "QUEST", "description": "Décrivez l'image mystère du jour.", "icon": "/static/animetix/img/ui/SAO.png", "gradient": "from-cyan-600 via-blue-500 to-sky-400", "completed": completed}, {"id": "blindtest", "brush1": "BLIND", "brush2": "TEST", "description": "Devinez l'animé du jour à partir de son opening/ending.", "icon": "/static/animetix/img/ui/Kaori.png", "gradient": "from-green-600 via-teal-500 to-emerald-400", "completed": completed}, {"id": "covertest", "brush1": "COVER", "brush2": "TEST", "description": "Devinez le manga du jour à partir de sa couverture.", "icon": "/static/animetix/img/ui/Bakuman.png", "gradient": "from-amber-600 via-yellow-500 to-orange-400", "completed": completed}]
    experimental = getattr(settings, 'FEATURE_FLAGS', {}).get('EXPERIMENTAL_MODES', False)
    if not experimental: modes_daily = [m for m in modes_daily if m['id'] not in ['paradox', 'vision_quest', 'akinetix']]
    return render(request, 'animetix/daily_selection.html', {'date': today, 'media_type': media_type, 'modes': modes_daily})

def custom_config_view(request):
    media_type, data = get_current_mode(request), animetix_service.load_data(get_current_mode(request))
    all_genres, all_tags = set(), set()
    if data:
        for item in data['db']: all_genres.update(item.get('genres', [])); all_tags.update(item.get('tags', []))
    return render(request, 'animetix/custom_config.html', {'whitelist': request.session.get('custom_whitelist', []), 'blacklist': request.session.get('custom_blacklist', []), 'genres_white': request.session.get('custom_genres_white', []), 'genres_black': request.session.get('custom_genres_black', []), 'tags_white': request.session.get('custom_tags_white', []), 'tags_black': request.session.get('custom_tags_black', []), 'mode': request.session.get('custom_mode', 'all'), 'all_genres': sorted(list(all_genres)), 'all_tags': sorted(list(all_tags))})

def save_custom_config(request):
    if request.method == 'POST':
        request.session.update({'custom_whitelist': request.POST.getlist('whitelist'), 'custom_blacklist': request.POST.getlist('blacklist'), 'custom_genres_white': request.POST.getlist('genres_white'), 'custom_genres_black': request.POST.getlist('genres_black'), 'custom_tags_white': request.POST.getlist('tags_white'), 'custom_tags_black': request.POST.getlist('tags_black'), 'custom_mode': request.POST.get('mode', 'all'), 'difficulty': 'Custom'})
        request.session.modified = True; return redirect('start_game')
    return redirect('custom_config')
