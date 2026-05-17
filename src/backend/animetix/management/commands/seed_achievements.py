from django.core.management.base import BaseCommand
from animetix.models import Achievement

class Command(BaseCommand):
    help = 'Seed the database with initial achievements'

    def handle(self, *args, **options):
        achievements = [
            {
                'code': 'first_win',
                'name': 'Première Victoire',
                'description': 'Gagnez votre toute première partie.',
                'icon': '🎯',
                'xp_reward': 100,
                'rarity': 'Common'
            },
            {
                'code': 'streak_3',
                'name': 'Triplé Gagnant',
                'description': 'Gagnez 3 parties consécutives.',
                'icon': '🔥',
                'xp_reward': 300,
                'rarity': 'Uncommon'
            },
            {
                'code': 'streak_7',
                'name': 'Inarrêtable',
                'description': 'Gagnez 7 parties consécutives.',
                'icon': '⚡',
                'xp_reward': 1000,
                'rarity': 'Rare'
            },
            {
                'code': 'wins_10',
                'name': 'Collectionneur',
                'description': 'Atteignez un total de 10 victoires.',
                'icon': '📚',
                'xp_reward': 500,
                'rarity': 'Uncommon'
            },
            {
                'code': 'wins_50',
                'name': 'Expert Animetix',
                'description': 'Atteignez un total de 50 victoires.',
                'icon': '🏆',
                'xp_reward': 2500,
                'rarity': 'Epic'
            },
            {
                'code': 'daily_master',
                'name': 'Maître du Quotidien',
                'description': 'Réussissez un défi quotidien.',
                'icon': '📅',
                'xp_reward': 200,
                'rarity': 'Common'
            },
            {
                'code': 'speed_demon',
                'name': 'Vitesse Éclair',
                'description': 'Trouvez le titre mystère en moins de 3 essais.',
                'icon': '🏎️',
                'xp_reward': 1500,
                'rarity': 'Legendary'
            },
            {
                'code': 'ranked_warrior',
                'name': 'Guerrier Classé',
                'description': 'Gagnez une partie en mode Classé.',
                'icon': '⚔️',
                'xp_reward': 300,
                'rarity': 'Uncommon'
            },
            {
                'code': 'streak_10',
                'name': 'Dieu du Jeu',
                'description': 'Gagnez 10 parties consécutives.',
                'icon': '👑',
                'xp_reward': 5000,
                'rarity': 'Legendary'
            },
            {
                'code': 'wins_100',
                'name': 'Légende Vivante',
                'description': 'Atteignez un total de 100 victoires.',
                'icon': '🌌',
                'xp_reward': 10000,
                'rarity': 'Legendary'
            },
            {
                'code': 'rare_finder',
                'name': 'Dénicheur de Pépites',
                'description': 'Trouvez une œuvre rare ou épique.',
                'icon': '💎',
                'xp_reward': 500,
                'rarity': 'Rare'
            },
            {
                'code': 'legendary_hunter',
                'name': 'Chasseur de Légendes',
                'description': 'Trouvez une œuvre légendaire.',
                'icon': '🐉',
                'xp_reward': 2000,
                'rarity': 'Legendary'
            },
            {
                'code': 'donor_bronze',
                'name': "Mécène d'Animetix",
                'description': 'Soutenez le projet avec votre premier don.',
                'icon': '☕',
                'xp_reward': 1000,
                'rarity': 'Rare'
            },
            {
                'code': 'donor_gold',
                'name': 'Gardien du Savoir',
                'description': 'Soutenez généreusement le projet pour maintenir l\'Oracle en ligne.',
                'icon': '🛡️',
                'xp_reward': 5000,
                'rarity': 'Legendary'
            }
        ]

        for data in achievements:
            obj, created = Achievement.objects.update_or_create(
                code=data['code'],
                defaults=data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Created achievement: {data['name']}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"🔄 Updated achievement: {data['name']}"))
