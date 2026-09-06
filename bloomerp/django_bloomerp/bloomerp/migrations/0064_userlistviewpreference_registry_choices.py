from django.db import migrations, models

import bloomerp.dataviews.registry


class Migration(migrations.Migration):
    dependencies = [("bloomerp", "0063_flatten_workflow_node_configuration")]

    operations = [
        migrations.AlterField(
            model_name="userlistviewpreference",
            name="view_type",
            field=models.CharField(
                choices=bloomerp.dataviews.registry.get_dataview_type_choices,
                default="table",
                max_length=50,
                verbose_name="View Type",
            ),
        ),
    ]
