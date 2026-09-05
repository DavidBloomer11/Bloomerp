

from bloomerp.communication.inbox_folder_definition import InboxFolderTypeDefinition
from bloomerp.utils.registry import BaseRegistry


class InboxFolderRegistry(BaseRegistry[InboxFolderTypeDefinition]):
    pass

INBOX_FOLDER_REGISTRY = InboxFolderRegistry(InboxFolderTypeDefinition)


# Register the inbox folder types here.

