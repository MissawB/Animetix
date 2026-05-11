import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')
django.setup()

from animetix.models import Achievement

def seed():
    achievements = [
        {
            "code": "FIRST_WIN",
            "name": "Premiers pas",
            "description": "Vous avez débloqué votre premier secret !",
            "icon": "bi-star",
            "rarity": "Common",
            "xp_reward": 100
        },
        {
            "code": "FLASH_WIN",
            "name": "L'Éclair de Konoha",
            "description": "Trouver un secret en moins de 30 secondes.",
            "icon": "bi-lightning-charge",
            "rarity": "Rare",
            "xp_reward": 250
        },
        {
            "code": "SURVIVOR",
            "name": "Le Survivant",
            "description": "Gagner après 20 tentatives ou plus.",
            "icon": "bi-shield-shaded",
            "rarity": "Common",
            "xp_reward": 150
        },
        {
            "code": "COLLECTOR_10",
            "name": "Collectionneur d'Elite",
            "description": "Avoir débloqué 10 secrets au total.",
            "icon": "bi-trophy",
            "rarity": "Rare",
            "xp_reward": 500
        },
        {
            "code": "DAILY_HERO",
            "name": "Héros du Jour",
            "description": "Compléter un défi quotidien.",
            "icon": "bi-calendar-check",
            "rarity": "Rare",
            "xp_reward": 200
        },
        {
            "code": "LEGENDARY_STREAK",
            "name": "Sannin Légendaire",
            "description": "Atteindre une série de 5 victoires quotidiennes consécutives.",
            "icon": "bi-fire",
            "rarity": "Legendary",
            "xp_reward": 1000
        }
    ]

    print("🌱 Initialisation du Grimoire des Hauts Faits...")
    for ach in achievements:
        obj, created = Achievement.objects.get_or_create(
            code=ach['code'],
            defaults=ach
        )
        if created:
            print(f"✅ Succès créé : {ach['name']}")
        else:
            print(f"ℹ️ Succès déjà existant : {ach['name']}")

    print("\n✨ Le Grimoire est prêt !")

if __name__ == "__main__":
    seed()
