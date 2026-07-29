from django.db import migrations, models


def copy_datetime_created_to_received(apps, schema_editor):
    InboxItem = apps.get_model("bloomerp", "InboxItem")
    InboxItem.objects.filter(datetime_received__isnull=True).update(
        datetime_received=models.F("datetime_created")
    )


class Migration(migrations.Migration):

    dependencies = [
        ("bloomerp", "0037_emailaccount_sync_state"),
    ]

    operations = [
        migrations.AddField(
            model_name="inboxitem",
            name="datetime_received",
            field=models.DateTimeField(
                blank=True,
                db_index=True,
                editable=False,
                help_text="Timestamp when the inbox item was received by its source system.",
                null=True,
            ),
        ),
        migrations.RunPython(copy_datetime_created_to_received, migrations.RunPython.noop),
    ]
