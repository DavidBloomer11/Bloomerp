# Generated by Django 5.1.1 on 2024-12-13 18:53

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bloomerp", "0056_documenttemplate_include_page_numbers_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="documenttemplate",
            name="footer",
            field=models.TextField(
                blank=True,
                help_text="Footer content of the document template.",
                null=True,
            ),
        ),
    ]