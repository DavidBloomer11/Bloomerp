from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bloomerp", "0055_alter_applicationfield_options_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tile",
            name="auto_generated",
            field=models.BooleanField(
                default=False,
                editable=False,
                verbose_name="Auto Generated",
            ),
        ),
    ]
