# Generated by Django 5.1.1 on 2024-09-15 22:16

import bloomerp.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bloomerp", "0005_alter_file_file"),
    ]

    operations = [
        migrations.AlterField(
            model_name="file",
            name="file",
            field=models.FileField(upload_to=bloomerp.models.File.upload_to),
        ),
    ]
