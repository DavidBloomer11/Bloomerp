import json

from bloomerp.communication.inbox_folder_definition import INBOX_ITEM_RENDER_TARGET, INBOX_ITEMS_TARGET, INBOX_MESSAGE_TARGET, InboxFolderType
from bloomerp.models.communication.inbox.inbox import Inbox
from bloomerp.models.communication.inbox.user_inbox_preference import UserInboxPreference
from bloomerp.views.base import BaseBloomerpView
from bloomerp.router import router
from django.db.models import Q
from django.views.generic import TemplateView

@router.register(
    path="/inbox",
    route_type="app",
    url_name="inbox",
    name="Inbox",
)
class InboxView(BaseBloomerpView, TemplateView):
    htmx_include_addendum_padding = False
    template_name = "views/communication/inbox.html"
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        inbox_preference = self.get_inbox_preference()
        ctx["inbox_types"] = [i.value for i in InboxFolderType if not i.value.source_model]
        ctx["inbox_preference"] = inbox_preference
        
        if inbox_preference and inbox_preference.selected_inbox_folder:
            folders = inbox_preference.selected_inbox.folders.all()
            selected_folder = inbox_preference.selected_inbox_folder
            folder_type = selected_folder.inbox_folder_type()
            filters = folder_type.resolve_filters(selected_folder)
            ctx["folder_options"] = [
                {
                    "folder": folder,
                    "subfolders": self.get_subfolder_filter_options(folder),
                }
                for folder in folders
            ]
            ctx["filters"] = [filter_definition for filter_definition in filters if not filter_definition.is_subfolder]
            actions = folder_type.actions or []
            ctx["actions"] = actions
            ctx["primary_actions"] = [action for action in actions if action.is_primary_action]
            ctx["secondary_actions"] = [action for action in actions if not action.is_primary_action]
        
        # Add targets
        ctx["targets"] = {
            "inbox_items" : INBOX_ITEMS_TARGET,
            "item_render" : INBOX_ITEM_RENDER_TARGET,
            "message" : INBOX_MESSAGE_TARGET,
        }
        
        return ctx

    def get_subfolder_filter_options(self, folder):
        return [
            {
                "key": filter_definition.key,
                "name": filter_definition.name,
                "filters_json": json.dumps(filter_definition.filters or {}),
            }
            for filter_definition in folder.inbox_folder_type().resolve_filters(folder)
            if filter_definition.is_subfolder
        ]
    
    def get_inbox_preference(self) -> UserInboxPreference | None:
        preference = (
            UserInboxPreference.objects
            .select_related("selected_inbox", "selected_inbox_folder")
            .filter(user=self.request.user)
            .first()
        )
        selected_inbox = preference.selected_inbox if preference else None
        if not selected_inbox:
            return None

        has_access = Inbox.objects.filter(
            Q(owner=self.request.user) | Q(members=self.request.user),
            pk=selected_inbox.pk,
        ).exists()
        return preference if has_access else None
    
    
