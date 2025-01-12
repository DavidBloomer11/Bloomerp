# Generated by Django 5.1.1 on 2024-10-02 22:48

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bloomerp", "0023_userdashboardview_layout"),
    ]

    operations = [
        migrations.CreateModel(
            name="Folder",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                (
                    "files",
                    models.ManyToManyField(related_name="folders", to="bloomerp.file"),
                ),
            ],
        ),
    ]