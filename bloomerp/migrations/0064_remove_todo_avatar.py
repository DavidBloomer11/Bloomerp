# Generated by Django 5.1.1 on 2025-01-08 00:09

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("bloomerp", "0063_rename_user_todo_requested_for_todo_title_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="todo",
            name="avatar",
        ),
    ]
