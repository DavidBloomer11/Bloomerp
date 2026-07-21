from __future__ import annotations

from django.db.models import Q, QuerySet

from bloomerp.communication.system_messages.base import SystemMessage


def resolve_workflow_notification_folders(
    *,
    workflow_run_id: str,
    **kwargs,
) -> QuerySet:
    from bloomerp.communication.inbox_folder_definition import InboxFolderType
    from bloomerp.models.automation.workflow_run import WorkflowRun
    from bloomerp.models.communication.inbox.inbox_folder import InboxFolder

    workflow_run = WorkflowRun.objects.select_related("workflow__created_by").get(
        pk=workflow_run_id
    )
    recipient_id = workflow_run.workflow.created_by_id
    if recipient_id is None:
        return InboxFolder.objects.none()

    return InboxFolder.objects.filter(
        Q(inbox__owner_id=recipient_id) | Q(inbox__members__id=recipient_id),
        type=InboxFolderType.IN_APP_NOTIFICATIONS.value.key,
    ).distinct()


def handle_workflow_result(
    folders: QuerySet,
    *,
    workflow_run_id: str,
    status: str,
    execution_trace: list[dict] | None = None,
    related_object=None,
    completed_at=None,
    **kwargs,
):
    from bloomerp.communication.inbox_sources import InboxSourceDelivery

    deliveries = []
    for folder in folders:
        item = SystemMessage.create_item(
            message_type="workflow",
            folder=folder,
            data={
                "workflow_run_id": workflow_run_id,
                "status": status,
                "execution_trace": execution_trace or [],
                "related_object": related_object,
                "completed_at": completed_at,
            },
        )
        deliveries.append(InboxSourceDelivery(folder=folder, items=(item,)))

    return tuple(deliveries)
