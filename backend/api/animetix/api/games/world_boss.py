import logging
from datetime import timedelta
from typing import Optional

from dependency_injector.wiring import Provide, inject
from django.db.models import F
from django.utils import timezone
from rest_framework import permissions, response, status, views

from ...containers import Container
from ...models import BossParticipation, GlobalBoss, Profile
from ...serializers import BossParticipationSerializer, GlobalBossSerializer

logger = logging.getLogger("animetix.worldboss")

BOSS_DURATION_DAYS = 7
BOSS_POOL_SIZE = 300  # Œuvres populaires uniquement : le raid doit rester trouvable.
BOSS_TOTAL_HP = 10000
ATTACK_DAMAGE = 100
LEADERBOARD_SIZE = 20


def _distribute_reward(boss: GlobalBoss) -> None:
    """Verse ``reward_xp`` à chaque participant, une seule fois par boss.

    Le drapeau ``reward_distributed`` est posé via un UPDATE conditionnel
    atomique : si deux requêtes portent le coup fatal en même temps, une seule
    remporte le flip et distribue — les autres n'ajoutent rien.
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


def _spawn_weekly_boss(catalog_service) -> Optional[GlobalBoss]:
    """Invoque le boss de la semaine.

    Sélection déterministe (catalogue trié par popularité + numéro de semaine
    ISO) : plusieurs instances/appels concurrents créent le même boss, sans
    besoin de planificateur externe. Le titre affiché est un nom de code — la
    réponse reste dans ``secret_title``.
    """
    data = catalog_service.load_data("Anime")
    pool = [
        it
        for it in (data or {}).get("db", [])[:BOSS_POOL_SIZE]
        if it.get("title") or it.get("name")
    ]
    if not pool:
        logger.warning("World Boss spawn impossible : catalogue vide.")
        return None

    now = timezone.now()
    iso = now.isocalendar()
    item = pool[(iso[0] * 100 + iso[1]) % len(pool)]

    hints = []
    if item.get("genres"):
        hints.append("Genres : " + ", ".join(item["genres"][:2]))
    if item.get("year"):
        hints.append(f"Année de sortie : {item['year']}")
    if item.get("studios"):
        hints.append(f"Studio : {item['studios'][0]}")

    boss = GlobalBoss.objects.create(
        title=f"RAID OMEGA · S{iso[1]:02d}",
        secret_title=item.get("title") or item.get("name"),
        media_type="Anime",
        total_hp=BOSS_TOTAL_HP,
        current_hp=BOSS_TOTAL_HP,
        community_hints=hints,
        end_date=now + timedelta(days=BOSS_DURATION_DAYS),
    )
    logger.info("World Boss de la semaine %s invoqué (id=%s).", iso[1], boss.id)
    return boss


class ActiveWorldBossView(views.APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @inject
    def get(self, request, catalog_service=Provide[Container.core.catalog_service]):
        now = timezone.now()
        boss = GlobalBoss.objects.filter(is_active=True, end_date__gt=now).first()
        if boss is None and not GlobalBoss.objects.filter(end_date__gt=now).exists():
            # Aucun raid en cours ni déjà vaincu cette semaine : on invoque
            # celui de la semaine. (Un boss vaincu garde end_date > now et
            # bloque le respawn — la communauté connaît déjà la réponse.)
            boss = _spawn_weekly_boss(catalog_service)

        if not boss:
            return response.Response(
                {"detail": "No active World Boss at the moment."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = GlobalBossSerializer(boss)
        return response.Response(serializer.data)


class WorldBossAttackView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        boss_id = request.data.get("boss_id")
        guess = request.data.get("guess")

        if not boss_id or not guess:
            return response.Response(
                {"detail": "boss_id and guess are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            boss = GlobalBoss.objects.get(id=boss_id, is_active=True)
        except GlobalBoss.DoesNotExist:
            return response.Response(
                {"detail": "Boss not found or inactive."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if boss.current_hp <= 0:
            return response.Response(
                {"detail": "Boss already defeated."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Simple logic: if guess matches secret_title, deal damage
        is_correct = guess.lower().strip() == boss.secret_title.lower().strip()

        damage = 0
        if is_correct:
            damage = ATTACK_DAMAGE
            boss.current_hp = max(0, boss.current_hp - damage)
            # Le signal post_save ne diffuse l'alerte globale que sur un vrai
            # changement de phase (marqueur consommé par broadcast_boss_phase).
            boss._phase_changed = boss.update_phase()
            if boss.current_hp <= 0:
                boss.is_active = (
                    False  # Vaincu — pas de respawn avant la semaine suivante.
                )
            boss.save()

            participation, created = BossParticipation.objects.get_or_create(
                user=request.user, boss=boss
            )
            participation.points_contributed += damage
            participation.save()

            if boss.current_hp <= 0:
                # Le finisher vient d'être enregistré : il touche la récompense
                # au même titre que les autres participants.
                _distribute_reward(boss)

        return response.Response(
            {
                "is_correct": is_correct,
                "damage_dealt": damage,
                "current_hp": boss.current_hp,
                "current_phase": boss.current_phase,
            }
        )


class WorldBossLeaderboardView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        boss_id = request.query_params.get("boss_id")
        if boss_id:
            boss = GlobalBoss.objects.filter(id=boss_id).first()
        else:
            # Par défaut : le raid en cours, sinon le plus récent (pour afficher
            # le classement d'un boss tout juste vaincu).
            boss = (
                GlobalBoss.objects.filter(is_active=True).first()
                or GlobalBoss.objects.order_by("-start_date").first()
            )
        if not boss:
            return response.Response({"boss_id": None, "leaderboard": []})

        top = (
            BossParticipation.objects.filter(boss=boss)
            .select_related("user")
            .order_by("-points_contributed")[:LEADERBOARD_SIZE]
        )
        return response.Response(
            {
                "boss_id": boss.id,
                "leaderboard": BossParticipationSerializer(top, many=True).data,
            }
        )
