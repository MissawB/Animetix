"""World Boss — a community raid fought with a quiz that doubles in difficulty.

The player climbs 12 tiers; tier N deals 2^(N-1) damage to a 100 000 HP boss shared
by everyone. One mistake drops them back to tier 1 — the damage already dealt stays.
Five correct answers at tier 12 open the Limiter Break: damage flat at 4096, no cap
on how obscure a work may be, six seconds on the clock.

Two rules are load-bearing and neither is negotiable:
  * The correct answer never leaves the server. The client posts an index; we correct.
  * The clock is the server's. `issued_at` is our timestamp, and an answer that comes
    back too late is wrong whatever the browser claims.

CPU only (the questions are drawn from the catalogue, never generated) → no Berrix.
"""

import logging
from datetime import timedelta
from typing import Optional

from core.domain.services.world_boss import rules
from dependency_injector.wiring import Provide, inject
from django.db.models import F
from django.db.models.functions import Greatest
from django.utils import timezone
from rest_framework import permissions, response, status, views

from animetix.api.dependencies import get_session_service
from animetix.api.throttles import CpuGameThrottle

from ...containers import Container
from ...models import BossParticipation, GlobalBoss, Profile
from ...serializers import BossParticipationSerializer, GlobalBossSerializer

logger = logging.getLogger("animetix.worldboss")

BOSS_DURATION_DAYS = 7
LEADERBOARD_SIZE = 20
SK = "wboss_"  # session-key prefix


def _now() -> float:
    """The server clock. Patched in tests; never read from the client."""
    return timezone.now().timestamp()


def _distribute_reward(boss: GlobalBoss) -> None:
    """Verse ``reward_xp`` à chaque participant, une seule fois par boss.

    Le drapeau ``reward_distributed`` est posé via un UPDATE conditionnel atomique :
    si deux requêtes portent le coup fatal en même temps, une seule remporte le flip.
    """
    claimed = GlobalBoss.objects.filter(id=boss.id, reward_distributed=False).update(
        reward_distributed=True
    )
    if not claimed:
        return
    user_ids = list(
        BossParticipation.objects.filter(boss=boss).values_list("user_id", flat=True)
    )
    if user_ids:
        Profile.objects.filter(user_id__in=user_ids).update(xp=F("xp") + boss.reward_xp)
    logger.info(
        "World Boss %s vaincu : %s XP versés à %d participant(s).",
        boss.id,
        boss.reward_xp,
        len(user_ids),
    )


def _spawn_weekly_boss() -> GlobalBoss:
    """Le raid de la semaine. Plus de titre secret : le boss n'est plus une devinette."""
    now = timezone.now()
    iso = now.isocalendar()
    boss = GlobalBoss.objects.create(
        title=f"RAID OMEGA · S{iso[1]:02d}",
        secret_title="",
        media_type="Anime",
        total_hp=rules.BOSS_TOTAL_HP,
        current_hp=rules.BOSS_TOTAL_HP,
        community_hints=[],
        end_date=now + timedelta(days=BOSS_DURATION_DAYS),
    )
    logger.info("World Boss de la semaine %s invoqué (id=%s).", iso[1], boss.id)
    return boss


def _active_boss() -> Optional[GlobalBoss]:
    now = timezone.now()
    boss = GlobalBoss.objects.filter(is_active=True, end_date__gt=now).first()
    if boss is None and not GlobalBoss.objects.filter(end_date__gt=now).exists():
        # Ni raid en cours ni raid déjà vaincu cette semaine.
        boss = _spawn_weekly_boss()
    return boss


def _reset_run(port, boss_id: int) -> None:
    port.set(SK + "boss_id", boss_id)
    port.set(SK + "tier", 1)
    port.set(SK + "streak", 0)
    port.set(SK + "limiter_break", False)
    port.set(SK + "run_damage", 0)
    port.set(SK + "correct_index", None)


class ActiveWorldBossView(views.APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [CpuGameThrottle]

    def get(self, request):
        boss = _active_boss()
        if not boss:
            return response.Response(
                {"detail": "No active World Boss at the moment."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return response.Response(GlobalBossSerializer(boss).data)


class WorldBossQuestionView(views.APIView):
    """Draws the next question of the run. The answer stays here."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [CpuGameThrottle]

    @inject
    def post(
        self,
        request,
        quiz_service=Provide[Container.core.world_boss_quiz_service],
    ):
        boss = _active_boss()
        if not boss or boss.current_hp <= 0:
            return response.Response(
                {"detail": "Boss already defeated."}, status=status.HTTP_404_NOT_FOUND
            )

        port = get_session_service(request).port
        if port.get(SK + "boss_id") != boss.id:
            _reset_run(port, boss.id)  # a new raid always starts a new run

        tier = port.get(SK + "tier", 1)
        limiter_break = bool(port.get(SK + "limiter_break", False))
        question = quiz_service.build_question(tier, limiter_break)

        port.set(SK + "correct_index", question.correct_index)
        port.set(SK + "correct_label", question.options[question.correct_index])
        port.set(SK + "subject", question.subject)
        port.set(SK + "issued_at", _now())

        participation = BossParticipation.objects.filter(
            user=request.user, boss=boss
        ).first()

        return response.Response(
            {
                "tier": tier,
                "band": rules.band_for(tier, limiter_break),
                "timer": rules.timer_for(tier, limiter_break),
                "damage": rules.damage_for(tier, limiter_break),
                "limiter_break": limiter_break,
                "streak": port.get(SK + "streak", 0),
                "run_damage": port.get(SK + "run_damage", 0),
                "best_tier": participation.best_tier if participation else 0,
                "archetype": question.archetype,
                "prompt": question.prompt,
                "options": question.options,
                "image": question.image,
            }
        )


class WorldBossAnswerView(views.APIView):
    """Corrects the pending question, applies the damage, moves the ladder."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [CpuGameThrottle]

    def post(self, request):
        port = get_session_service(request).port
        correct_index = port.get(SK + "correct_index")
        if correct_index is None:
            return response.Response(
                {"detail": "No question in progress."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Consume the question BEFORE scoring it: a replayed request must not be able
        # to cash the same answer twice.
        port.set(SK + "correct_index", None)

        boss = _active_boss()
        if not boss or boss.current_hp <= 0:
            return response.Response(
                {"detail": "Boss already defeated."}, status=status.HTTP_404_NOT_FOUND
            )

        tier = port.get(SK + "tier", 1)
        limiter_break = bool(port.get(SK + "limiter_break", False))
        streak = port.get(SK + "streak", 0)
        run_damage = port.get(SK + "run_damage", 0)
        correct_label = port.get(SK + "correct_label", "")

        elapsed = _now() - (port.get(SK + "issued_at") or 0)
        late = elapsed > rules.timer_for(tier, limiter_break) + rules.GRACE_SECONDS
        chosen = request.data.get("index")
        correct = (not late) and isinstance(chosen, int) and chosen == correct_index

        damage = 0
        broke_limiter = False
        if correct:
            damage = rules.damage_for(tier, limiter_break)
            run_damage += damage

            GlobalBoss.objects.filter(id=boss.id).update(
                current_hp=Greatest(F("current_hp") - damage, 0)
            )
            boss.refresh_from_db()
            boss._phase_changed = boss.update_phase()
            if boss.current_hp <= 0:
                boss.is_active = (
                    False  # vaincu : pas de respawn avant la semaine suivante
                )
            boss.save(update_fields=["current_phase", "is_active"])

            if tier >= rules.MAX_TIER and not limiter_break:
                streak += 1
                if streak >= rules.LIMITER_STREAK:
                    limiter_break = True
                    broke_limiter = True
            next_tier = rules.next_tier(tier)
        else:
            # Mort subite : on retombe au palier 1. Les dégâts déjà infligés restent.
            next_tier, streak, limiter_break, run_damage = 1, 0, False, 0

        participation, _ = BossParticipation.objects.get_or_create(
            user=request.user, boss=boss
        )
        participation.points_contributed += damage
        participation.best_tier = max(participation.best_tier, tier if correct else 0)
        if broke_limiter:
            participation.limiter_breaks += 1
        participation.save()

        if correct and boss.current_hp <= 0:
            _distribute_reward(boss)

        port.set(SK + "tier", next_tier)
        port.set(SK + "streak", streak)
        port.set(SK + "limiter_break", limiter_break)
        port.set(SK + "run_damage", run_damage)

        return response.Response(
            {
                "correct": correct,
                "late": late,
                "damage_dealt": damage,
                "correct_index": correct_index,
                "correct_label": correct_label,
                "subject": port.get(SK + "subject", ""),
                "tier": next_tier,
                "run_damage": run_damage,
                "best_tier": participation.best_tier,
                "limiter_break": limiter_break,
                "streak": streak,
                "boss": {
                    "current_hp": boss.current_hp,
                    "total_hp": boss.total_hp,
                    "current_phase": boss.current_phase,
                    "is_active": boss.is_active,
                },
            }
        )


class WorldBossLeaderboardView(views.APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [CpuGameThrottle]

    def get(self, request):
        boss_id = request.query_params.get("boss_id")
        if boss_id:
            boss = GlobalBoss.objects.filter(id=boss_id).first()
        else:
            boss = (
                GlobalBoss.objects.filter(is_active=True).first()
                or GlobalBoss.objects.order_by("-start_date").first()
            )
        if not boss:
            return response.Response({"boss_id": None, "leaderboard": []})

        top = (
            BossParticipation.objects.filter(boss=boss)
            .select_related("user")
            .order_by("-best_tier", "-points_contributed")[:LEADERBOARD_SIZE]
        )
        return response.Response(
            {
                "boss_id": boss.id,
                "leaderboard": BossParticipationSerializer(top, many=True).data,
            }
        )
