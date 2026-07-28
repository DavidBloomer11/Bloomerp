import json

from bloomerp.communication.inbox_folder_definition import INBOX_ITEM_RENDER_TARGET, INBOX_ITEMS_TARGET, INBOX_MESSAGE_TARGET, InboxFolderType
from bloomerp.models.communication.inbox.inbox import Inbox
from bloomerp.models.communication.inbox.user_inbox_preference import UserInboxPreference
from bloomerp.services.preference_services import PreferenceManager
from bloomerp.views.base import BaseBloomerpView
from bloomerp.router import router
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
        preference_manager = PreferenceManager(self.request.user)
        inbox = preference_manager.get_or_create_selected(
            Inbox,
            force_create=False,
        )
        inbox_preference = self.get_inbox_preference(inbox)
        ctx["inbox_types"] = [i.value for i in InboxFolderType if not i.value.source_model]
        ctx["inbox"] = inbox
        ctx["inbox_preference"] = inbox_preference
        ctx["can_manage_inbox"] = bool(
            inbox and preference_manager.can_manage(inbox)
        )
        
        if inbox and inbox_preference and inbox_preference.selected_inbox_folder:
            folders = inbox.folders.all()
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
            ctx["filters"] = [
                self._serialize_filter_option(filter_definition)
                for filter_definition in filters
                if not filter_definition.is_subfolder
            ]
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
            self._serialize_filter_option(filter_definition)
            for filter_definition in folder.inbox_folder_type().resolve_filters(folder)
            if filter_definition.is_subfolder
        ]

    def _serialize_filter_option(self, filter_definition) -> dict[str, object]:
        """Serialize one inbox filter for safe use in a data attribute."""
        return {
            "key": filter_definition.key,
            "name": filter_definition.name,
            "filters_json": json.dumps(
                filter_definition.filters or {},
                separators=(",", ":"),
            ),
        }
    
    def get_inbox_preference(
        self,
        inbox: Inbox | None,
    ) -> UserInboxPreference | None:
        if inbox is None:
            return None

        preference = UserInboxPreference.get_for_user(self.request.user)
        selected_folder = (
            inbox.folders.filter(pk=preference.selected_inbox_folder_id).first()
            if preference.selected_inbox_folder_id
            else None
        )
        if selected_folder is None:
            selected_folder = inbox.folders.order_by("pk").first()
            preference.selected_inbox_folder = selected_folder
            preference.save(update_fields=["selected_inbox_folder"])
        return preference
    
    
