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
from datetime import datetime, timedelta, timezone as dt_timezone
from typing import Optional

from core.domain.exceptions import GameLogicError
from core.domain.services.world_boss import rules
from dependency_injector.wiring import Provide, inject
from django.db.models import F, Value
from django.db.models.functions import Greatest
from django.utils import timezone
from rest_framework import permissions, response, status, views

from animetix.api.throttles import CpuGameThrottle

from ...containers import Container
from ...models import BossParticipation, GlobalBoss, Profile
from ...serializers import BossParticipationSerializer, GlobalBossSerializer

logger = logging.getLogger("animetix.worldboss")

BOSS_DURATION_DAYS = 7
LEADERBOARD_SIZE = 20


def _now() -> float:
    """The server clock. Patched in tests; never read from the client."""
    return timezone.now().timestamp()


def _now_dt() -> datetime:
    """The same clock, as a datetime — so `issued_at` and the deadline agree."""
    return datetime.fromtimestamp(_now(), tz=dt_timezone.utc)


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


PENDING_FIELDS = (
    "pending_index",
    "pending_label",
    "pending_subject",
    "pending_options",
    "pending_prompt",
    "pending_archetype",
    "pending_image",
    "issued_at",
)

CLEARED_PENDING = {
    "pending_index": None,
    "pending_label": "",
    "pending_subject": "",
    "pending_options": [],
    "pending_prompt": "",
    "pending_archetype": "",
    "pending_image": None,
    "issued_at": None,
}


def _deadline(participation: BossParticipation) -> float:
    """When the pending question expires, on the server clock."""
    return (
        participation.issued_at.timestamp()
        + rules.timer_for(participation.tier, participation.limiter_break)
        + rules.GRACE_SECONDS
    )


def _question_payload(participation: BossParticipation) -> dict:
    """The public view of the pending question. `pending_index` never appears here,
    and neither does `pending_subject`: the reveal comes with the answer."""
    tier = participation.tier
    limiter_break = participation.limiter_break
    return {
        "tier": tier,
        "band": rules.band_for(tier, limiter_break),
        "timer": rules.timer_for(tier, limiter_break),
        "damage": rules.damage_for(tier, limiter_break),
        "limiter_break": limiter_break,
        "streak": participation.streak,
        "run_damage": participation.run_damage,
        "best_tier": participation.best_tier,
        "archetype": participation.pending_archetype,
        "prompt": participation.pending_prompt,
        "options": participation.pending_options,
        "image": participation.pending_image,
    }


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

        # La participation est la course : par (joueur, boss), côté serveur. Un
        # nouveau raid = une nouvelle ligne = une nouvelle course, gratuitement.
        participation, _ = BossParticipation.objects.get_or_create(
            user=request.user, boss=boss
        )

        if participation.pending_index is not None and participation.issued_at:
            if _now() <= _deadline(participation):
                # Re-tirer la question serait un re-roll gratuit : le joueur
                # redemanderait jusqu'à tomber sur l'archétype qu'il sait traiter.
                # On ré-émet la MÊME question, sans re-tamponner l'horloge.
                return response.Response(_question_payload(participation))

            # Le délai est écoulé : c'est un raté. Fermer l'onglet ne doit ni
            # bloquer le joueur, ni lui faire échapper à la sanction.
            participation.tier = 1
            participation.streak = 0
            participation.limiter_break = False
            participation.run_damage = 0
            for field, value in CLEARED_PENDING.items():
                setattr(participation, field, value)
            participation.save(
                update_fields=["tier", "streak", "limiter_break", "run_damage"]
                + list(PENDING_FIELDS)
            )

        tier = participation.tier
        limiter_break = participation.limiter_break
        try:
            question = quiz_service.build_question(tier, limiter_break)
        except GameLogicError:
            # Catalogue trop pauvre pour composer une question : c'est une panne de
            # service, pas un bug — 503 plutôt qu'un 500 opaque.
            logger.warning("World Boss: no question available at tier %s.", tier)
            return response.Response(
                {"detail": "No question available right now."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        participation.pending_index = question.correct_index
        participation.pending_label = question.options[question.correct_index]
        participation.pending_subject = question.subject
        participation.pending_options = list(question.options)
        participation.pending_prompt = question.prompt
        participation.pending_archetype = question.archetype
        participation.pending_image = question.image
        participation.issued_at = _now_dt()
        participation.save(update_fields=list(PENDING_FIELDS))

        return response.Response(_question_payload(participation))


class WorldBossAnswerView(views.APIView):
    """Corrects the pending question, applies the damage, moves the ladder."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [CpuGameThrottle]

    def post(self, request):
        boss = _active_boss()
        if not boss or boss.current_hp <= 0:
            return response.Response(
                {"detail": "Boss already defeated."}, status=status.HTTP_404_NOT_FOUND
            )

        # La participation est résolue depuis le boss ACTIF. Une question tirée pour
        # le raid précédent vit sur la ligne du raid précédent : elle n'existe donc
        # tout simplement pas ici, et ne peut pas frapper le boss frais.
        participation = BossParticipation.objects.filter(
            user=request.user, boss=boss
        ).first()
        # Same guard as the /question/ path: `_deadline()` reads `issued_at`
        # unguarded, so a half-set row (pending_index set, issued_at not --
        # or vice versa) must be treated as "no question in progress" here
        # too, instead of reaching _deadline() and raising on None.timestamp().
        if (
            participation is None
            or participation.pending_index is None
            or participation.issued_at is None
        ):
            return response.Response(
                {"detail": "No question in progress."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # On lit la question AVANT de la consommer : c'est ce que fait aussi la
        # requête concurrente. Le départage vient ensuite, et de la base seule.
        correct_index = participation.pending_index
        correct_label = participation.pending_label
        subject = participation.pending_subject
        tier = participation.tier
        limiter_break = participation.limiter_break
        streak = participation.streak
        run_damage = participation.run_damage
        deadline = _deadline(participation)
        now = _now()

        # Le verrou, c'est le rowcount : deux requêtes simultanées ont lu le même
        # `pending_index`, une seule remporte l'UPDATE conditionnel. L'autre repart
        # avec un 400 — et surtout, sans infliger le moindre dégât.
        claimed = BossParticipation.objects.filter(
            pk=participation.pk, pending_index__isnull=False
        ).update(pending_index=None)
        if not claimed:
            return response.Response(
                {"detail": "No question in progress."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        late = now > deadline
        chosen = request.data.get("index")
        correct = (not late) and isinstance(chosen, int) and chosen == correct_index

        damage = 0
        dealt = 0
        broke_limiter = False
        if correct:
            damage = rules.damage_for(tier, limiter_break)

            boss.refresh_from_db(fields=["current_hp"])
            hp_before = boss.current_hp
            GlobalBoss.objects.filter(id=boss.id).update(
                current_hp=Greatest(F("current_hp") - damage, 0)
            )
            # L'overkill ne compte pas : 4096 sur un boss à 1 PV, c'est 1 point de
            # dégâts infligé — pas 4096 crédités au classement.
            dealt = min(damage, max(hp_before, 0))
            run_damage += dealt

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

        updates = dict(
            CLEARED_PENDING,
            tier=next_tier,
            streak=streak,
            limiter_break=limiter_break,
            run_damage=run_damage,
            last_participation=timezone.now(),  # auto_now ne s'applique pas à update()
            # F() / Greatest(): deux réponses du même joueur en parallèle ne
            # doivent pas se marcher dessus (un read-modify-write en perdrait une).
            points_contributed=F("points_contributed") + dealt,
            best_tier=Greatest(F("best_tier"), Value(tier if correct else 0)),
        )
        if broke_limiter:
            updates["limiter_breaks"] = F("limiter_breaks") + 1
        BossParticipation.objects.filter(pk=participation.pk).update(**updates)
        participation.refresh_from_db()

        if correct and boss.current_hp <= 0:
            _distribute_reward(boss)

        return response.Response(
            {
                "correct": correct,
                "late": late,
                "damage_dealt": dealt,
                "correct_index": correct_index,
                "correct_label": correct_label,
                "subject": subject,
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
