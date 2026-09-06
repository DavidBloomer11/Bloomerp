from django.db import migrations


def rename_gant_key(apps, schema_editor):
    UserListViewPreference = apps.get_model("bloomerp", "UserListViewPreference")

    for preference in UserListViewPreference.objects.filter(view_type="gant"):
        preference.view_type = "gantt"
        for field_name in ("display_fields", "options"):
            values = getattr(preference, field_name) or {}
            if "gant" in values:
                values["gantt"] = values.pop("gant")
                setattr(preference, field_name, values)
        preference.save(update_fields=["view_type", "display_fields", "options"])


def restore_gant_key(apps, schema_editor):
    UserListViewPreference = apps.get_model("bloomerp", "UserListViewPreference")

    for preference in UserListViewPreference.objects.filter(view_type="gantt"):
        preference.view_type = "gant"
        for field_name in ("display_fields", "options"):
            values = getattr(preference, field_name) or {}
            if "gantt" in values:
                values["gant"] = values.pop("gantt")
                setattr(preference, field_name, values)
        preference.save(update_fields=["view_type", "display_fields", "options"])


class Migration(migrations.Migration):
    dependencies = [("bloomerp", "0065_merge_20260906_1959")]

    operations = [migrations.RunPython(rename_gant_key, restore_gant_key)]
