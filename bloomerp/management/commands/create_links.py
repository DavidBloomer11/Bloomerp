from django.core.management.base import BaseCommand
from bloomerp.utils.models import (
    get_create_view_url,
    get_list_view_url,
    get_detail_view_url,
    get_update_view_url,
    get_bulk_upload_view_url,
    get_model_dashboard_view_url,
    get_document_template_generate_view_url,
    get_document_template_list_view_url
)

class Command(BaseCommand):
    help = 'Generate links for all views in the application'

    def handle(self, *args, **options):
        pass