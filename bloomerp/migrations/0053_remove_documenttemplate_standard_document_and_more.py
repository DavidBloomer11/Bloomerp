# Generated by Django 5.1.1 on 2024-12-08 22:49

import bloomerp.models.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bloomerp", "0052_alter_sqlquery_options"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="documenttemplate",
            name="standard_document",
        ),
        migrations.AlterField(
            model_name="documenttemplate",
            name="footer",
            field=models.TextField(
                blank=True, help_text="Footer of the document template.", null=True
            ),
        ),
        migrations.AlterField(
            model_name="documenttemplate",
            name="free_variables",
            field=models.ManyToManyField(
                blank=True,
                help_text="A free variable is a variable that is not from a model, and can be inserted in the template at creation time.",
                null=True,
                to="bloomerp.documenttemplatefreevariable",
            ),
        ),
        migrations.AlterField(
            model_name="documenttemplate",
            name="model_variable",
            field=models.ForeignKey(
                default=1,
                help_text="Model variable of the document template.",
                on_delete=django.db.models.deletion.CASCADE,
                to="contenttypes.contenttype",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="documenttemplate",
            name="name",
            field=models.CharField(
                help_text="Name of the document template.", max_length=100
            ),
        ),
        migrations.AlterField(
            model_name="documenttemplate",
            name="styling",
            field=models.ForeignKey(
                blank=True,
                help_text="Styling of the document template.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="bloomerp.documenttemplatestyling",
            ),
        ),
        migrations.AlterField(
            model_name="documenttemplate",
            name="template",
            field=bloomerp.models.fields.TextEditorField(
                default="Hello world",
                help_text="Content of the template, including the variables.",
            ),
        ),
        migrations.AlterField(
            model_name="documenttemplate",
            name="template_header",
            field=models.ForeignKey(
                blank=True,
                help_text="Header of the document template.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="bloomerp.documenttemplateheader",
            ),
        ),
        migrations.AlterField(
            model_name="documenttemplateheader",
            name="header",
            field=models.ImageField(
                help_text="Image of the header.", upload_to="document_templates/headers"
            ),
        ),
        migrations.AlterField(
            model_name="documenttemplateheader",
            name="name",
            field=models.CharField(
                help_text="Name of the template header.", max_length=100
            ),
        ),
    ]