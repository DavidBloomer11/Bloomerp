from django.db.models import Q

from bloomerp.communication.system_messages.base import SystemMessage


def resolve_system_message_folders(
    *,
    user_ids: list[int | str],
    **kwargs,
):
    from bloomerp.communication.inbox_folder_definition import InboxFolderType
    from bloomerp.models.communication.inbox.inbox_folder import InboxFolder

    return InboxFolder.objects.filter(
        Q(inbox__owner_id__in=user_ids) | Q(inbox__members__id__in=user_ids),
        type=InboxFolderType.IN_APP_NOTIFICATIONS.value.key,
    ).distinct()


def handle_system_message(
    folders,
    *,
    system_message_type: str,
    data: dict,
    **kwargs,
):
    from bloomerp.communication.inbox_sources import (
        InboxSourceDelivery,
        InboxSourceExecutionResult,
    )

    deliveries = []
    for folder in folders:
        item = SystemMessage.create_item(
            message_type=system_message_type,
            folder=folder,
            data=data,
        )
        deliveries.append(InboxSourceDelivery(folder=folder, items=(item,)))
    return InboxSourceExecutionResult(deliveries=tuple(deliveries))
