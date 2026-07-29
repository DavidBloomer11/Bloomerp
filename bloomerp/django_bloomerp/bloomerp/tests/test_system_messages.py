from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from bloomerp.automation.defintion import WorkflowNodeType
from bloomerp.communication.inbox_folder_definition import InboxFolderType
from bloomerp.communication.system_messages.base import SystemMessage
from bloomerp.models.automation import Workflow, WorkflowNode, WorkflowRun, WorkflowRunStep
from bloomerp.models.automation.workflow_run_step import WorkflowRunStepStatus
from bloomerp.models.communication.inbox.inbox import Inbox
from bloomerp.models.communication.inbox.inbox_folder import InboxFolder
from bloomerp.models.communication.inbox.inbox_item import InboxItem
from bloomerp.services.workflow_services import run_workflow


class WorkflowSystemMessageTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="workflow-notification-user",
            email="workflow-notification@example.com",
            password="password",
        )
        inbox = Inbox.objects.create(user=self.user, name="Notifications")
        self.folder = InboxFolder.objects.create(
            inbox=inbox,
            type=InboxFolderType.IN_APP_NOTIFICATIONS.value.key,
        )
        self.workflow = Workflow.objects.create(
            name="Update customer score",
            created_by=self.user,
            updated_by=self.user,
            enable_logging=True,
        )
        self.trigger = WorkflowNode.objects.create(
            workflow=self.workflow,
            name="Customer updated",
            type=WorkflowNodeType.TRIGGER.value.id,
            config={"sub_type": "HUMAN_TRIGGER", "parameters": {}},
            pos_x=0,
            pos_y=0,
        )
        self.action = WorkflowNode.objects.create(
            workflow=self.workflow,
            name="Enrich customer",
            type=WorkflowNodeType.ACTION.value.id,
            config={"sub_type": "ENRICH_DATA", "parameters": {"data": {}}},
            pos_x=300,
            pos_y=0,
        )
        self.workflow.connect_nodes(self.trigger, self.action)

    def test_workflow_message_renders_from_snapshot_after_run_is_deleted(self):
        """
        Use case: A workflow notification is opened after its workflow run was deleted.
        Expected result: The stored snapshot still renders the complete notification.
        """
        # 1. Create a completed workflow run with measurable step timings.
        workflow_run = WorkflowRun.objects.create(workflow=self.workflow)
        first_step = WorkflowRunStep.objects.create(
            workflow_run=workflow_run,
            sequence=0,
            action_id="HUMAN_TRIGGER",
            status=WorkflowRunStepStatus.COMPLETED,
        )
        second_step = WorkflowRunStep.objects.create(
            workflow_run=workflow_run,
            sequence=1,
            action_id="ENRICH_DATA",
            status=WorkflowRunStepStatus.COMPLETED,
        )
        now = timezone.now()
        WorkflowRun.objects.filter(pk=workflow_run.pk).update(
            datetime_created=now - timedelta(seconds=5),
        )
        workflow_run.refresh_from_db()
        WorkflowRunStep.objects.filter(pk=first_step.pk).update(
            datetime_created=now - timedelta(seconds=4),
            datetime_updated=now - timedelta(seconds=3),
        )
        WorkflowRunStep.objects.filter(pk=second_step.pk).update(
            datetime_created=now - timedelta(seconds=2),
            datetime_updated=now,
        )

        # 2. Create a workflow system message containing a durable snapshot.
        item = SystemMessage.create_item(
            message_type="workflow",
            folder=self.folder,
            data={
                "workflow_run_id": str(workflow_run.pk),
                "status": "successful",
                "completed_at": now,
                "related_object": self.user,
                "execution_trace": [
                    {
                        "node_id": self.trigger.id,
                        "node_sub_type": "HUMAN_TRIGGER",
                        "status": "success",
                    },
                    {
                        "node_id": self.action.id,
                        "node_sub_type": "ENRICH_DATA",
                        "status": "success",
                    },
                ],
            },
        )

        # 3. Verify that the snapshot contains the render-critical data.
        snapshot = item.raw_meta_data["workflow"]
        self.assertEqual(item.raw_meta_data["system_message_type"], "workflow")
        self.assertEqual(snapshot["step_count"], 2)
        self.assertEqual(len(snapshot["graph"]["nodes"]), 2)
        self.assertEqual(len(snapshot["graph"]["edges"]), 1)
        self.assertGreaterEqual(snapshot["duration_seconds"], 5)
        self.assertEqual(snapshot["related_object"]["object_id"], str(self.user.pk))

        # 4. Delete the live run and render the notification from its snapshot.
        workflow_run.delete()
        item.refresh_from_db()
        rendered = SystemMessage.resolve_render(item)

        self.assertIn("Update customer score", rendered)
        self.assertIn("Execution time", rendered)
        self.assertIn("Execution graph", rendered)
        self.assertIn("original workflow-run record is no longer available", rendered)
        self.assertIn("workflow-notification-user", rendered)

        # 5. Verify that trusted system-message content renders directly.
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("components_render_inbox_item", kwargs={"item_id": item.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Execution graph")
        self.assertNotContains(response, "<iframe")

    def test_invalid_system_message_type_is_rejected(self):
        """
        Use case: A caller requests an unregistered system message type.
        Expected result: Message creation fails with a descriptive validation error.
        """
        # 1. Attempt to create a message with an unknown registry key.
        with self.assertRaisesRegex(ValueError, "Invalid system message type"):
            SystemMessage.create_item(
                message_type="unknown",
                folder=self.folder,
                data={},
            )

    @patch("bloomerp.communication.inbox_sources.send_user_inbox_message")
    def test_workflow_execution_publishes_a_workflow_result_message(
        self,
        send_user_inbox_message,
    ):
        """
        Use case: A workflow finishes successfully.
        Expected result: A workflow notification is persisted and broadcast once.
        """
        # 1. Execute the workflow through the public workflow service.
        workflow_run = run_workflow(self.workflow, {})

        # 2. Verify the notification snapshot and real-time broadcast.
        item = InboxItem.objects.get(
            folder=self.folder,
            related_item_id=str(workflow_run.pk),
        )
        self.assertEqual(item.raw_meta_data["system_message_type"], "workflow")
        self.assertEqual(item.raw_meta_data["workflow"]["status"], "completed")
        self.assertEqual(item.raw_meta_data["workflow"]["step_count"], 2)
        send_user_inbox_message.assert_called_once()
