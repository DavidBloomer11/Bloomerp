from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bloomerp", "0036_remove_user_file_view_preference_inbox_inboxfolder_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="emailaccount",
            name="provider",
            field=models.CharField(choices=[("imap", "IMAP / SMTP")], default="imap", max_length=32),
        ),
        migrations.AddField(
            model_name="emailaccount",
            name="last_sync_error",
            field=models.TextField(blank=True, editable=False),
        ),
        migrations.AddField(
            model_name="emailaccount",
            name="last_sync_finished_at",
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="emailaccount",
            name="last_sync_started_at",
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="emailaccount",
            name="next_sync_at",
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="emailaccount",
            name="sync_cursor",
            field=models.JSONField(blank=True, default=dict, help_text="Provider-specific cursor/state for incremental synchronization."),
        ),
        migrations.AddField(
            model_name="emailaccount",
            name="sync_enabled",
            field=models.BooleanField(default=True, help_text="Whether this account should be synchronized automatically."),
        ),
        migrations.AddField(
            model_name="emailaccount",
            name="sync_interval_minutes",
            field=models.PositiveIntegerField(default=5, help_text="Polling interval used by providers that synchronize on a schedule."),
        ),
        migrations.AddField(
            model_name="emailaccount",
            name="sync_locked_until",
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="emailaccount",
            name="sync_mode",
            field=models.CharField(blank=True, choices=[("polling", "Polling"), ("push", "Push")], help_text="Synchronization mode for this account. Defaults to the provider's preferred mode.", max_length=32),
        ),
        migrations.AddIndex(
            model_name="emailaccount",
            index=models.Index(fields=["status", "sync_enabled", "next_sync_at"], name="email_acc_sync_due_idx"),
        ),
    ]
