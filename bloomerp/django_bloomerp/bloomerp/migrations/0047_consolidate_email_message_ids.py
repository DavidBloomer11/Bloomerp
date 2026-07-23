from django.db import migrations, models


def consolidate_email_message_ids(apps, schema_editor):
    InboxItem = apps.get_model("bloomerp", "InboxItem")
    current_folder_id = None
    keepers = {}
    email_items = InboxItem.objects.filter(item_type="email").order_by(
        "folder_id",
        "datetime_created",
        "id",
    )

    for item in email_items.iterator(chunk_size=1000):
        if item.folder_id != current_folder_id:
            current_folder_id = item.folder_id
            keepers = {}

        metadata = item.raw_meta_data if isinstance(item.raw_meta_data, dict) else {}
        message_id = str(metadata.get("message_id") or "").strip()
        provider = str(metadata.get("provider") or "imap")
        mailbox = str(metadata.get("mailbox") or "INBOX")
        provider_message_id = str(
            metadata.get("provider_message_id")
            or item.related_item_id
            or ""
        )
        related_item_id = (
            message_id
            if message_id
            else f"{provider}:{mailbox}:{provider_message_id}"
        )

        locations = dict(metadata.get("locations") or {})
        if provider_message_id:
            locations[mailbox] = {
                "mailbox": mailbox,
                "provider_message_id": provider_message_id,
                "flags": metadata.get("flags") or [],
                "raw": metadata.get("raw") or {},
            }

        canonical_metadata = dict(metadata)
        for location_field in ("provider_message_id", "mailbox", "flags", "raw"):
            canonical_metadata.pop(location_field, None)
        canonical_metadata["locations"] = locations

        keeper = keepers.get(related_item_id)
        if keeper is None:
            keeper = item
            keepers[related_item_id] = keeper
            keeper.related_item_id = related_item_id
            keeper.raw_meta_data = canonical_metadata
            keeper.save(update_fields=["related_item_id", "raw_meta_data"])
            continue

        keeper_metadata = dict(keeper.raw_meta_data or {})
        keeper_locations = dict(keeper_metadata.get("locations") or {})
        keeper_locations.update(locations)
        keeper_metadata["locations"] = keeper_locations
        keeper.raw_meta_data = keeper_metadata

        update_fields = ["raw_meta_data"]
        if item.is_read and not keeper.is_read:
            keeper.is_read = True
            update_fields.append("is_read")
        if (
            item.datetime_received
            and (
                keeper.datetime_received is None
                or item.datetime_received < keeper.datetime_received
            )
        ):
            keeper.datetime_received = item.datetime_received
            update_fields.append("datetime_received")
        keeper.save(update_fields=update_fields)
        item.delete()


def set_constraints_immediate_on_postgresql(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("SET CONSTRAINTS ALL IMMEDIATE")


class Migration(migrations.Migration):

    dependencies = [
        ("bloomerp", "0046_merge_20260721_0721"),
    ]

    operations = [
        migrations.AlterField(
            model_name="inboxitem",
            name="related_item_id",
            field=models.CharField(
                blank=True,
                help_text=(
                    "Optional reference to the source item's ID, if applicable."
                ),
                max_length=1000,
                null=True,
            ),
        ),
        migrations.RunPython(
            consolidate_email_message_ids,
            migrations.RunPython.noop,
        ),
        migrations.RunPython(
            set_constraints_immediate_on_postgresql,
            migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name="inboxitem",
            constraint=models.UniqueConstraint(
                condition=models.Q(
                    item_type="email",
                    related_item_id__isnull=False,
                ),
                fields=("folder", "item_type", "related_item_id"),
                name="uniq_email_item_identity",
            ),
        ),
    ]
