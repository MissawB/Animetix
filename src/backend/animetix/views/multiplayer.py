import random
import string
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .common import animetix_service, langchain_service, handle_win_achievements
from ..utils import get_current_mode
from ..models import DuelRoom, GlobalBoss, BossParticipation
from ..forms import GameGuessForm
from ..services import DIFFICULTY_SETTINGS

def undercover_party_setup(request): return render(request, 'animetix/undercover/undercover_setup.html', {'media_type': get_current_mode(request)})
def undercover_online_join(request):
    if request.method == 'POST': return redirect('undercover_online_room', room_code=(request.POST.get('room_code', '').upper().strip() or ''.join(random.choices("ABCDE123", k=4))))
    return redirect('undercover_party_setup')
def undercover_online_room(request, room_code): return render(request, 'animetix/undercover/online_room.html', {'room_code': room_code, 'media_type': get_current_mode(request), 'difficulty': request.session.get('difficulty', 'Normal')})
def codemanga_setup(request): return render(request, 'animetix/codemanga/setup.html', {'media_type': get_current_mode(request)})
def codemanga_room(request, room_code): return render(request, 'animetix/codemanga/room.html', {'room_code': room_code, 'difficulty': request.GET.get('difficulty', 'Normal')})
def codemanga_game(request, room_code): return render(request, 'animetix/codemanga/game.html', {'room_code': room_code, 'difficulty': request.GET.get('difficulty', 'Normal')})

def undercover_party_play(request):
    if request.method == 'POST':
        media, num, diff = get_current_mode(request), int(request.POST.get('num_players', 4)), request.session.get('difficulty', 'Normal')
        player_ids = [str(i+1) for i in range(num)]
        game_data = animetix_service.game_service.start_undercover_game(media_type=media, difficulty=diff, player_ids=player_ids, rank_limits=DIFFICULTY_SETTINGS)
        if not game_data: return redirect('index')
        players = []
        for p_id, assignment in game_data['assignments'].items():
            try: display_id = int(p_id)
            except ValueError:
                numeric_part = ''.join(filter(str.isdigit, p_id))
                display_id = int(numeric_part) if numeric_part else random.randint(1, 1000)
            players.append({"id": display_id, "role": assignment['role'], "title": assignment['word'], "image": assignment['image']})
        clue = langchain_service.generate_undercover_clue(media, game_data['civil_word'], game_data['undercover_word'], request.session.get('language', 'Français')) if langchain_service else "..."
        return render(request, 'animetix/undercover/undercover_party.html', {'num_players': num, 'players': players, 'clue': clue, 'icon': "🦙", 'difficulty': diff})
    return redirect('index')

@login_required
def create_duel(request):
    media_type, data = get_current_mode(request), animetix_service.load_data(get_current_mode(request))
    code, secret = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6)), random.choice(data.get('titles', ['Naruto']))
    DuelRoom.objects.create(room_code=code, player1=request.user, media_type=media_type, secret_title=secret)
    return redirect('duel_room', room_code=code)

@login_required
def join_duel(request):
    if request.method == 'POST':
        code = request.POST.get('room_code', '').upper().strip()
        try:
            duel = DuelRoom.objects.get(room_code=code, is_finished=False)
            if duel.player1 != request.user: duel.player2 = request.user; duel.save()
            return redirect('duel_room', room_code=code)
        except DuelRoom.DoesNotExist: return redirect('index')
    return render(request, 'animetix/social/join_duel.html')

@login_required
def duel_room_view(request, room_code):
    try:
        duel = DuelRoom.objects.get(room_code=room_code)
        return render(request, 'animetix/social/duel_room.html', {'duel': duel, 'is_p1': duel.player1 == request.user})
    except DuelRoom.DoesNotExist: return redirect('index')

@login_required
def finish_duel(request, room_code):
    try:
        duel = DuelRoom.objects.get(room_code=room_code)
        if request.user in [duel.player1, duel.player2]:
            duel.is_finished = True; duel.save()
            from ..tasks import cleanup_duel_resources_task
            cleanup_duel_resources_task.delay(room_code)
            return JsonResponse({'status': 'duel_finished'})
    except DuelRoom.DoesNotExist: pass
    return redirect('index')

def global_boss_view(request):
    boss = GlobalBoss.objects.filter(is_active=True).first()
    if not boss: return redirect('index')
    participations, user_participation = BossParticipation.objects.filter(boss=boss).order_by('-points_contributed')[:10], None
    if request.user.is_authenticated: user_participation = BossParticipation.objects.filter(user=request.user, boss=boss).first()
    hp_percent = (boss.current_hp / boss.total_hp) * 100 if boss.total_hp > 0 else 100
    return render(request, 'animetix/boss/boss.html', {'boss': boss, 'hp_percent': hp_percent, 'participations': participations, 'user_participation': user_participation, 'txt': animetix_service.translations.get(request.session.get('language', 'Français'), {})})

def global_boss_guess(request):
    if request.method == 'POST' and request.user.is_authenticated:
        form = GameGuessForm(request.POST)
        if form.is_valid():
            guess_title = form.cleaned_data['guess']
            boss = GlobalBoss.objects.filter(is_active=True, current_hp__gt=0).first()
            if not boss: return redirect('global_boss')
            data = animetix_service.load_data(boss.media_type)
            if not data: return redirect('global_boss')
            raw_sim = animetix_service.game_service.calculate_raw_similarity(boss.media_type, boss.secret_title, guess_title, data)
            damage_mult = 1.0
            if boss.current_phase == 2: damage_mult = 0.7
            elif boss.current_phase == 3: damage_mult = 0.4
            damage = int(raw_sim * 100 * damage_mult)
            if guess_title == boss.secret_title: damage = boss.current_hp
            boss.current_hp = max(0, boss.current_hp - damage); phase_changed = boss.update_phase(); boss.save()
            part, _ = BossParticipation.objects.get_or_create(user=request.user, boss=boss)
            part.points_contributed += damage; part.save()
            if boss.current_hp <= 0: boss.is_active = False; boss.save(); request.user.profile.xp += boss.reward_xp; request.user.profile.save()
            if request.headers.get('HX-Request'): return render(request, 'animetix/boss/boss_fragment.html', {'boss': boss, 'damage': damage, 'phase_changed': phase_changed, 'hp_percent': (boss.current_hp / boss.total_hp) * 100 if boss.total_hp > 0 else 0})
    return redirect('global_boss')
