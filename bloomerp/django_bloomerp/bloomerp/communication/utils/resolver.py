


from typing import TYPE_CHECKING, Type

from bloomerp.models.communication.inbox.inbox_folder import InboxFolder
from bloomerp.models.communication.inbox.inbox_item import InboxItem



def resolve_item(item:str|InboxFolder|InboxItem, target:Type[InboxFolder] | Type[InboxItem]) -> InboxFolder|InboxItem:    
    if isinstance(item, str):
        return target.objects.get(id=item)
    elif isinstance(item, (InboxFolder, InboxItem)):
        return item
    else:
        raise TypeError("Item must be a string ID, InboxFolder, or InboxItem instance.")