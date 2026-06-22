from django.core.management.base import BaseCommand

from animetix.services import restore_brain_service


class Command(BaseCommand):
    help = "Restores the animetix-brain Cloud Run GPU service scale count."

    def add_arguments(self, parser):
        parser.add_argument(
            "--max-instances",
            type=int,
            default=3,
            help="Maximum instance count to restore the service to (matches the --max-instances ceiling in scripts/deploy/deploy_brain.py)",
        )

    def handle(self, *args, **options):
        max_instances = options["max_instances"]
        self.stdout.write(
            f"Restoring animetix-brain with maxInstanceCount={max_instances}..."
        )

        success, message = restore_brain_service(max_instances)
        if success:
            self.stdout.write(
                self.style.SUCCESS(f"Successfully restored service: {message}")
            )
        else:
            self.stderr.write(self.style.ERROR(f"Failed to restore service: {message}"))
