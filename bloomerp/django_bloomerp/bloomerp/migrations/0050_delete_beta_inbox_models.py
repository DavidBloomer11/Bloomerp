from django.db import migrations


class Migration(migrations.Migration):
    """Discard the beta inbox schema before recreating its preference model."""

    dependencies = [
        ("bloomerp", "0049_workflowrunstep_node_alter_workflowrunstep_status"),
    ]

    operations = [
        migrations.DeleteModel(name="UserInboxPreference"),
        migrations.DeleteModel(name="InboxItem"),
        migrations.DeleteModel(name="InboxFolder"),
        migrations.DeleteModel(name="Inbox"),
    ]
