from bloomerp.communication.inbox_sources import publish_event

from bloomerp.automation.base_executor import BaseExecutor
from bloomerp.automation.schema import WorkflowInputRequirement, WorkflowIOSchema, WorkflowValueType
from django.forms import Form
from django import forms

# TODO: Choices should be defined in a central place
class SendUserMessageForm(Form):
    user_id = forms.CharField(
        help_text="Use a literal user id or a value reference like {{ input.id }}.",
    )
    message = forms.CharField(widget=forms.Textarea)
    message_type = forms.ChoiceField(
        choices=[
            ("success", "Success"),
            ("info", "Info"),
            ("warning", "Warning"),
            ("error", "Error"),
        ],
    )

class SendUserMessage(BaseExecutor):
    config_form = SendUserMessageForm
    input_requirement = WorkflowInputRequirement(
        value_type="any",
        label="Any input",
        description="Use upstream references to pick the recipient user or message text.",
    )
    output_schema = WorkflowIOSchema(
        value_type=WorkflowValueType.NONE,
        label="No output",
    )
    
    def execute(self, input_data: dict) -> dict:
        params = self.resolve_config(input_data)
        user_id = params.get("user_id")
        
        publish_event(
            key="system.message",
            user_ids=[user_id],
            system_message_type="general",
            data={
                "message": str(params.get("message")),
                "severity": params.get("message_type") or "info",
            },
        )
        
        
        
        
