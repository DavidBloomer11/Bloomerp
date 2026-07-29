from django.db import migrations


def repair_workflow_run_step_schema(apps, schema_editor):
    workflow_run_step = apps.get_model("bloomerp", "WorkflowRunStep")

    with schema_editor.connection.cursor() as cursor:
        columns = {
            column.name
            for column in schema_editor.connection.introspection.get_table_description(
                cursor,
                workflow_run_step._meta.db_table,
            )
        }

    for field_name in ("state", "output_file"):
        field = workflow_run_step._meta.get_field(field_name)
        if field.column not in columns:
            schema_editor.add_field(workflow_run_step, field)


class Migration(migrations.Migration):
    dependencies = [
        (
            "bloomerp",
            "0052_remove_userdetailviewpreference_content_type_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(
            repair_workflow_run_step_schema,
            migrations.RunPython.noop,
        ),
    ]
