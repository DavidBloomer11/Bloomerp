from django.db import migrations, models

import bloomerp.automation.registry


def flatten_workflow_node_configuration(apps, schema_editor):
    WorkflowNode = apps.get_model("bloomerp", "WorkflowNode")

    for node in WorkflowNode.objects.all().iterator():
        config = node.config
        if not isinstance(config, dict):
            raise ValueError(f"WorkflowNode {node.pk} config must be an object")
        if not isinstance(config.get("sub_type"), str) or not config["sub_type"]:
            raise ValueError(
                f"WorkflowNode {node.pk} config must contain a non-empty sub_type"
            )
        if "parameters" not in config:
            raise ValueError(f"WorkflowNode {node.pk} config is missing parameters")
        if not isinstance(config["parameters"], dict):
            raise ValueError(f"WorkflowNode {node.pk} parameters must be an object")

        node.sub_type = config["sub_type"]
        node.parameters = config["parameters"]
        node.save(update_fields=["sub_type", "parameters"])


def nest_workflow_node_configuration(apps, schema_editor):
    WorkflowNode = apps.get_model("bloomerp", "WorkflowNode")

    for node in WorkflowNode.objects.all().iterator():
        node.config = {
            "sub_type": node.sub_type,
            "parameters": node.parameters,
        }
        node.save(update_fields=["config"])


class Migration(migrations.Migration):
    dependencies = [("bloomerp", "0062_communication_registry_choices")]

    operations = [
        migrations.AddField(
            model_name="workflownode",
            name="sub_type",
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="workflownode",
            name="parameters",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="The parameters for the workflow node.",
                verbose_name="Parameters",
            ),
        ),
        migrations.RunPython(
            flatten_workflow_node_configuration,
            nest_workflow_node_configuration,
        ),
        migrations.AlterField(
            model_name="workflownode",
            name="sub_type",
            field=models.CharField(
                choices=bloomerp.automation.registry.workflow_node_sub_type_choices,
                db_index=True,
                help_text="The registered subtype of the workflow node.",
                max_length=100,
                verbose_name="Sub Type",
            ),
        ),
        migrations.RemoveField(
            model_name="workflownode",
            name="config",
        ),
        migrations.AlterField(
            model_name="workflownode",
            name="type",
            field=models.CharField(
                choices=bloomerp.automation.registry.workflow_node_type_choices,
                help_text="The type of the workflow node.",
                max_length=32,
                verbose_name="Type",
            ),
        ),
    ]
