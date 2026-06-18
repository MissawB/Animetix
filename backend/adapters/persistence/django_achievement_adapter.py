import logging
from typing import List

from animetix.models import Achievement, UserAchievement
from core.domain.entities.achievement import AchievementDefinition
from core.ports.achievement_port import AchievementPort
from django.contrib.auth.models import User

logger = logging.getLogger("animetix")


class DjangoAchievementAdapter(AchievementPort):
    def get_all_achievements(self) -> List[AchievementDefinition]:
        achievements = Achievement.objects.all()
        return [
            AchievementDefinition(
                code=a.code,
                name=a.name,
                description=a.description,
                icon=a.icon,
                xp_reward=a.xp_reward,
                rarity=a.rarity,
            )
            for a in achievements
        ]

    def get_user_unlocked_codes(self, user_id: int) -> List[str]:
        return list(
            UserAchievement.objects.filter(user_id=user_id).values_list(
                "achievement__code", flat=True
            )
        )

    def unlock_achievement(self, user_id: int, achievement_code: str) -> None:
        try:
            user = User.objects.get(id=user_id)
            achievement = Achievement.objects.get(code=achievement_code)

            # Enregistrement du déblocage
            UserAchievement.objects.get_or_create(user=user, achievement=achievement)

            # Attribution de l'XP
            profile = user.profile
            profile.xp += achievement.xp_reward
            profile.save()

            logger.info(
                f"🏆 Achievement Unlocked: {achievement.name} for {user.username}"
            )
        except Exception as e:
            logger.error(
                f"❌ Error unlocking achievement {achievement_code} for user {user_id}: {e}"
            )
