

from bloomerp.communication.inbox_folder_definition import (
    InboxFolderType,
    InboxFolderTypeDefinition,
)
from bloomerp.utils.registry import BaseRegistry


class InboxFolderRegistry(BaseRegistry[InboxFolderTypeDefinition]):
    pass

INBOX_FOLDER_REGISTRY = InboxFolderRegistry(InboxFolderTypeDefinition)

INBOX_FOLDER_REGISTRY.register("ALL", InboxFolderType.ALL.value)
INBOX_FOLDER_REGISTRY.register(
    "IN_APP_NOTIFICATIONS",
    InboxFolderType.IN_APP_NOTIFICATIONS.value,
)
INBOX_FOLDER_REGISTRY.register("EMAIL", InboxFolderType.EMAIL.value)

