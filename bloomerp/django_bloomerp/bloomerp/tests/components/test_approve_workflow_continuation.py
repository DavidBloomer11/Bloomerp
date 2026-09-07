# TESTREFAC

from unittest.mock import patch

from django.contrib.auth.models import Group
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse

from bloomerp.models import User
from bloomerp.models.automation import Workflow, WorkflowNode
from bloomerp.models.automation.workflow_run import WorkflowRun
from bloomerp.models.automation.workflow_run_step import (
    WorkflowRunStep,
    WorkflowRunStepStatus,
)


class ApproveWorkflowContinuationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="workflow-approver",
            password="password",
        )
        self.workflow = Workflow.objects.create(name="Approval workflow")
        self.approval_node = WorkflowNode.objects.create(
            workflow=self.workflow,
            type="ACTION",
            sub_type="HUMAN_IN_THE_LOOP",
            parameters={},
        )
        self.workflow_run = WorkflowRun.objects.create(workflow=self.workflow)
        WorkflowRunStep.objects.create(
            workflow_run=self.workflow_run,
            node=self.approval_node,
            sequence=1,
            action_id="HUMAN_IN_THE_LOOP",
            status=WorkflowRunStepStatus.PAUSED,
        )
        self.client.force_login(self.user)

    def request_component(self):
        with (
            patch(
                "bloomerp.components.automation.approve_workflow_continuation.load_step_output",
                return_value={},
            ),
            patch(
                "bloomerp.components.automation.approve_workflow_continuation.render_blank_form",
                return_value=HttpResponse("Approval form"),
            ),
        ):
            return self.client.get(
                reverse(
                    "components_automation_approve_workflow_continuation",
                    kwargs={"workflow_run_id": self.workflow_run.id},
                )
            )

    def set_approvers(self, *, users=None, groups=None):
        self.approval_node.parameters = {
            "approver_users": users or [],
            "approver_groups": groups or [],
        }
        self.approval_node.save(update_fields=["parameters"])

    def test_returns_403_when_user_has_no_approval_access(self):
        response = self.request_component()

        self.assertEqual(response.status_code, 403)

    def test_allows_an_explicitly_configured_approver_user(self):
        self.set_approvers(users=[self.user.id])

        response = self.request_component()

        self.assertEqual(response.status_code, 200)

    def test_allows_a_user_in_a_configured_approver_group(self):
        group = Group.objects.create(name="Workflow approvers")
        self.user.groups.add(group)
        self.set_approvers(groups=[group.id])

        response = self.request_component()

        self.assertEqual(response.status_code, 200)

    def test_allows_a_user_with_change_access_to_the_workflow(self):
        self.user.is_superuser = True
        self.user.save(update_fields=["is_superuser"])

        response = self.request_component()

        self.assertEqual(response.status_code, 200)
