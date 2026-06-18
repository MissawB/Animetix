from django.utils import timezone
from rest_framework import permissions, response, status, views

from ...models import BossParticipation, GlobalBoss
from ...serializers import GlobalBossSerializer


class ActiveWorldBossView(views.APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        boss = GlobalBoss.objects.filter(
            is_active=True, end_date__gt=timezone.now()
        ).first()
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

        # Simple logic: if guess matches secret_title, deal damage
        is_correct = guess.lower().strip() == boss.secret_title.lower().strip()

        damage = 0
        if is_correct:
            damage = 100  # Fixed damage for now
            boss.current_hp = max(0, boss.current_hp - damage)
            boss.update_phase()
            boss.save()

            participation, created = BossParticipation.objects.get_or_create(
                user=request.user, boss=boss
            )
            participation.points_contributed += damage
            participation.save()

        return response.Response(
            {
                "is_correct": is_correct,
                "damage_dealt": damage,
                "current_hp": boss.current_hp,
                "current_phase": boss.current_phase,
            }
        )
