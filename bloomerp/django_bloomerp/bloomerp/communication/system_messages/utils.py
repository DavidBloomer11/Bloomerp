from dataclasses import dataclass
from typing import Self

from bloomerp.models.users.user import AbstractBloomerpUser
from bloomerp.utils.base_type_definition import BaseTypeDefinition
from bloomerp.utils.realtime import send_user_message
from django.db import models
from django.db.models import Q

SYSTEM_MESSAGE_ACTOR = "System"

@dataclass
class SystemMessageDefinition:
    key: str
    name: str
    

class SystemMessage(BaseTypeDefinition):
    
    GENERAL = SystemMessageDefinition(
        key="general",
        name="General",
        
    )
    
    @classmethod
    def send_message(
        cls, 
        type:str,
        users: models.QuerySet[AbstractBloomerpUser],
        message: str,
    ):
        from bloomerp.models.communication.inbox.inbox_item import InboxItem
        from bloomerp.models.communication.inbox.inbox_folder import InboxFolder
        from bloomerp.communication.inbox_folder_definition import InboxFolderType
        
        message_type : "Self" = cls.from_key(type)
        if not message_type:
            raise ValueError(f"Invalid system message type: {type}")
        
        folders = InboxFolder.objects.filter(
            Q(inbox__owner__in=users) | Q(inbox__members__in=users),
            type=InboxFolderType.IN_APP_NOTIFICATIONS.value.key,
        ).distinct()
        
        for folder in folders:
            InboxItem.objects.create(
                title="A message",
                snippet="Some snippet",
                item_type=InboxFolderType.IN_APP_NOTIFICATIONS.value.item_type.key,
                folder=folder,
                actor=SYSTEM_MESSAGE_ACTOR,
            )
        
        
        
        
        
        
    