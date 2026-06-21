from django.core.management.base import BaseCommand

from animetix.models import VoiceProfile

# Importation des profils hardcodés existants
try:
    from pipeline.mlops.songs_and_seiyuu_db import SEIYUU_PROFILES
except ImportError:
    SEIYUU_PROFILES = {}

try:
    from pipeline.mlops.french_market_db import FRENCH_VOICE_ACTORS
except ImportError:
    FRENCH_VOICE_ACTORS = {}

# Banque d'échantillons de démonstration publics hébergés sur Hugging Face ou GitHub
# Ces fichiers serviront de base de démonstration pour le lazy-loading
PUBLIC_VOICE_SAMPLES = {
    "Goku": "https://huggingface.co/datasets/taresh18/AnimeVox/resolve/main/audio/goku_sample.wav",
    "Naruto": "https://huggingface.co/datasets/taresh18/AnimeVox/resolve/main/audio/naruto_sample.wav",
    "Luffy": "https://huggingface.co/datasets/taresh18/AnimeVox/resolve/main/audio/luffy_sample.wav",
    "Saber": "https://huggingface.co/datasets/taresh18/AnimeVox/resolve/main/audio/saber_sample.wav",
    "Rem": "https://huggingface.co/datasets/taresh18/AnimeVox/resolve/main/audio/rem_sample.wav",
}


class Command(BaseCommand):
    help = "Indexation des datasets vocaux et initialisation de la base de données des voix."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force la ré-indexation et le remplacement des profils existants.",
        )

    def handle(self, *args, **options):
        force = options["force"]

        if force:
            self.stdout.write("Suppression des profils vocaux existants...")
            VoiceProfile.objects.all().delete()

        created_count = 0
        updated_count = 0

        # 1. Indexation des Seiyuus Japonais (depuis songs_and_seiyuu_db.py)
        self.stdout.write("Indexation des Seiyuus Japonais...")
        for name, details in SEIYUU_PROFILES.items():
            # Fallback URL d'échantillon ou mockup si manquant
            fallback_sample_url = PUBLIC_VOICE_SAMPLES.get(
                name.split()[0],  # Assaye de matcher le premier mot (ex: Goku, Naruto)
                "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",  # Fallback audio standard
            )

            profile, created = VoiceProfile.objects.update_or_create(
                name=name,
                defaults={
                    "language": "japanese",
                    "origin": "dataset",
                    "definition": details.get("definition", ""),
                    "roles": details.get("examples", ""),
                    "impact": details.get("impact", "N/A"),
                    "origin_detail": fallback_sample_url,
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        # 2. Indexation des Doubleurs Français (depuis french_market_db.py)
        self.stdout.write("Indexation des Doubleurs Français (VF)...")
        for name, details in FRENCH_VOICE_ACTORS.items():
            fallback_sample_url = (
                "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3"
            )

            profile, created = VoiceProfile.objects.update_or_create(
                name=name,
                defaults={
                    "language": "french",
                    "origin": "dataset",
                    "definition": details.get("definition", ""),
                    "roles": details.get("examples", ""),
                    "impact": details.get("impact", "N/A"),
                    "origin_detail": fallback_sample_url,
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        # 3. Indexation des personnages additionnels du dataset public AnimeVox
        self.stdout.write("Indexation des personnages additionnels issus du Dataset...")
        EXTRA_CHARACTERS = {
            "Paimon": {
                "lang": "japanese",
                "definition": "Compagnon de voyage dans Genshin Impact, voix suraiguë et expressive.",
                "roles": "Paimon (Genshin Impact)",
                "url": "https://huggingface.co/datasets/taresh18/AnimeVox/resolve/main/audio/paimon_sample.wav",
            },
            "Hu Tao": {
                "lang": "japanese",
                "definition": "Directrice de la maison funéraire Wangsheng, ton enjoué et excentrique.",
                "roles": "Hu Tao (Genshin Impact)",
                "url": "https://huggingface.co/datasets/taresh18/AnimeVox/resolve/main/audio/hutao_sample.wav",
            },
            "Eren Yeager": {
                "lang": "japanese",
                "definition": "Protagoniste de L'Attaque des Titans, ton déterminé et haineux.",
                "roles": "Eren Yeager (Attack on Titan)",
                "url": PUBLIC_VOICE_SAMPLES["Luffy"],  # Fallback de test
            },
        }

        for name, info in EXTRA_CHARACTERS.items():
            profile, created = VoiceProfile.objects.update_or_create(
                name=name,
                defaults={
                    "language": info["lang"],
                    "origin": "dataset",
                    "definition": info["definition"],
                    "roles": info["roles"],
                    "impact": "SOTA",
                    "origin_detail": info["url"],
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Indexation terminee. Crees: {created_count}, Mis a jour: {updated_count}"
            )
        )
