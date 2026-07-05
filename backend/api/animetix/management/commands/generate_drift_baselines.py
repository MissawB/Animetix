from django.core.management.base import BaseCommand

from animetix.containers import get_container

# Collections vectorielles suivies par le rapport de dérive.
COLLECTIONS = ("anime", "manga", "character")


class Command(BaseCommand):
    help = (
        "Fige la distribution actuelle des embeddings de chaque collection comme "
        "baseline de détection de dérive (data/artifacts/baselines/*.npy). À lancer "
        "après un cycle d'entraînement validé : le rapport de dérive (page "
        "Transparence) affiche alors un vrai test KS au lieu de « unknown ». "
        "Ne PAS planifier fréquemment — une baseline régénérée à chaque run "
        "annulerait toute détection (elle serait toujours égale à l'état courant)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--collection",
            action="append",
            dest="collections",
            choices=COLLECTIONS,
            help="Limite à une collection (répétable). Par défaut : toutes.",
        )

    def handle(self, *args, **options):
        drift_service = get_container().core.drift_service()
        collections = options.get("collections") or list(COLLECTIONS)

        written = 0
        for coll in collections:
            self.stdout.write(f"Génération de la baseline de dérive pour « {coll} »…")
            try:
                drift_service.generate_new_baseline(coll)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"  Échec pour « {coll} » : {e}"))
                continue

            # generate_new_baseline n'écrit rien si la collection est vide ; on
            # vérifie l'état résultant pour un compte-rendu honnête.
            report = drift_service.check_collection_drift(coll)
            if report.get("status") == "unknown":
                self.stdout.write(
                    self.style.WARNING(
                        f"  « {coll} » : aucun embedding trouvé — baseline non écrite."
                    )
                )
            else:
                written += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  « {coll} » : baseline définie "
                        f"({report.get('sample_size', '?')} vecteurs)."
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(f"Terminé — {written} baseline(s) écrite(s).")
        )
