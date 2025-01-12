# Generated by Django 5.1.1 on 2024-12-16 13:00

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bloomerp", "0057_alter_documenttemplate_footer"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="documenttemplate",
            name="model_variable",
            field=models.ForeignKey(
                blank=True,
                help_text="Model variable of the document template. Can be used to parse objects from the model into the template.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="contenttypes.contenttype",
            ),
        ),
    ]