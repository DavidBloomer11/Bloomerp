from django.db import migrations, models

import bloomerp.field_types.registry


class Migration(migrations.Migration):
    dependencies = [("bloomerp", "0060_add_bulk_add_permission")]

    operations = [
        migrations.AlterField(
            model_name="applicationfield",
            name="field_type",
            field=models.CharField(
                choices=bloomerp.field_types.registry.field_type_choices,
                help_text="The type of the field.",
                max_length=100,
                verbose_name="Field Type",
            ),
        ),
    ]
