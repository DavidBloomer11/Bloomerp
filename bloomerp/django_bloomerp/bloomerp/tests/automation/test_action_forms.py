from django.contrib.auth import get_user_model
from django.test import SimpleTestCase

from bloomerp.automation.actions.human_in_the_loop import HumanInTheLoopForm
from bloomerp.automation.actions.send_user_message import SendUserMessageForm


class WorkflowActionFormTests(SimpleTestCase):
    def test_human_in_the_loop_resolves_user_model_when_form_is_initialized(self):
        self.assertIsNone(
            HumanInTheLoopForm.base_fields["approver_users"].widget.model
        )

        form = HumanInTheLoopForm()

        self.assertIs(
            form.fields["approver_users"].widget.model,
            get_user_model(),
        )

    def test_send_user_message_resolves_user_model_when_form_is_initialized(self):
        self.assertIsNone(SendUserMessageForm.base_fields["users"].widget.model)

        form = SendUserMessageForm()

        self.assertIs(
            form.fields["users"].widget.model,
            get_user_model(),
        )
