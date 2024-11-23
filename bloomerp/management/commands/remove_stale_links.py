# myapp/management/commands/list_urls.py

from django.core.management.base import BaseCommand
from django.urls import get_resolver, URLPattern, URLResolver
from bloomerp.models import Link
from bloomerp.models import Workspace

class Command(BaseCommand):
    help = 'Removes all stale links from the database'

    def handle(self, *args, **kwargs):
        links = Link.objects.filter(is_absolute_url=False)

        length = 0
        delete_links:list[Link] = []

        # Remove all links that are not valid
        for link in links:
            if not link.is_valid():
                delete_links.append(link)

        # For each workspace, remove all links that are not valid
        if delete_links:
            length = len(delete_links)

            for workspace in Workspace.objects.all():
                workspace.remove_links_from_content(delete_links)

            # Delete all links that are not valid
            for link in delete_links:
                link.delete()
        

        self.stdout.write(self.style.SUCCESS(f'Successfully {length} removed all stale links'))

    