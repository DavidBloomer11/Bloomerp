# Generated by Django 5.1.1 on 2024-09-23 21:45

import bloomerp.models.fields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("bloomerp", "0018_documenttemplatestyling_documenttemplate_styling"),
    ]

    operations = [
        migrations.AlterField(
            model_name="documenttemplatestyling",
            name="styling",
            field=bloomerp.models.fields.CodeField(default="", language="css"),
        ),
    ]