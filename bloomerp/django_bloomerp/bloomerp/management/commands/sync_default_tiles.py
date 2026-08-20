from django.core.management.base import BaseCommand

from bloomerp.services.workspace_services import create_or_update_default_tiles


class Command(BaseCommand):
    help = "Create or update tiles declared on BloomERP modules and models."

    def handle(self, *args, **options):
        tiles = create_or_update_default_tiles()
        self.stdout.write(
            self.style.SUCCESS(f"Synchronized {len(tiles)} default tile(s).")
        )
