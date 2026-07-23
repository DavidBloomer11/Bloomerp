from bloomerp.communication.inbox_sources import publish_event

from bloomerp.automation.base_executor import BaseExecutor
from bloomerp.automation.schema import WorkflowInputRequirement, WorkflowIOSchema, WorkflowValueType
from django.forms import Form
from django import forms

from bloomerp.widgets.foreign_field_widget import ForeignFieldWidget
from django.contrib.auth import get_user_model

# TODO: Choices should be defined in a central place
class SendUserMessageForm(Form):
    users = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=ForeignFieldWidget(
            model=get_user_model(),
            attrs={
                "is_m2m" : True,
                "class" : "input w-full"
            }    
        ),
        
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
        users = params.get("users", [])
        
        publish_event(
            key="system.message",
            user_ids=users,
            system_message_type="general",
            data={
                "message": str(params.get("message")),
                "severity": params.get("message_type") or "info",
            },
        )
        
        
        
        
        
        
