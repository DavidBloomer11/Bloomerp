from django import forms

from bloomerp.automation.base_executor import BaseExecutor
from bloomerp.automation.schema import (
    WorkflowIOFlowKind,
    WorkflowInputRequirement,
    WorkflowIOSchema,
    WorkflowValueField,
    WorkflowValueType,
)


class CollectForm(forms.Form):
    pass


def _as_collected_item_field(field: WorkflowValueField) -> WorkflowValueField:
    if field.path == "input":
        path = "0"
    elif field.path.startswith("input."):
        path = f"0.{field.path.removeprefix('input.')}"
    else:
        path = f"0.{field.path}" if field.path else "0"

    return WorkflowValueField(
        path=path,
        label=field.label,
        value_type=field.value_type,
        description=field.description,
        optional=field.optional,
        children=[
            _as_collected_item_field(child)
            for child in field.children
        ],
    )


class CollectExecutor(BaseExecutor):
    """Collapse the current for-each fan-out into one ordered list."""

    config_form = CollectForm
    input_requirement = WorkflowInputRequirement(
        value_type=WorkflowValueType.ANY,
        label="Item result",
        description="Collects one result from each iteration of the current For Each.",
    )

    def execute(self, trigger_data):
        return trigger_data

    @classmethod
    def get_output_schema(
        cls,
        config: dict | None = None,
        input_schema: WorkflowIOSchema | None = None,
    ) -> WorkflowIOSchema:
        fields = []
        if input_schema is not None:
            fields = [
                _as_collected_item_field(field)
                for field in input_schema.fields
            ]
            if not fields:
                fields = [
                    WorkflowValueField(
                        path="0",
                        label=input_schema.label or "Collected item",
                        value_type=input_schema.value_type,
                    )
                ]

        return WorkflowIOSchema(
            value_type=WorkflowValueType.LIST,
            flow_kind=WorkflowIOFlowKind.NORMAL,
            label="Collected results",
            description="Outputs all iteration results once, ordered by item index.",
            fields=fields,
        )
