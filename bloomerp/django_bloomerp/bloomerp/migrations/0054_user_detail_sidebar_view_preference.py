from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bloomerp", "0053_repair_workflow_run_step_schema"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="detail_sidebar_view_preference",
            field=models.CharField(
                choices=[("activity", "Activity"), ("comments", "Comments")],
                default="activity",
                help_text="The detail view sidebar panel to show first",
                max_length=20,
            ),
        ),
    ]
