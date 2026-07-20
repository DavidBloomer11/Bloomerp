import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("bloomerp", "0044_alter_userobjectlayoutpreference_unique_together"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserDetailViewTabsPreference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(default="Default", help_text="Optional name for this preference, for user reference", max_length=255)),
                ("selected", models.BooleanField(default=False, help_text="Indicates if this preference is currently selected for the user. Only one preference per user can be selected at a time.")),
                ("initial_default", models.BooleanField(default=False, help_text="Indicates if this preference is the initial default for the user. This is used to determine the user's default preference when they first create an account.")),
                ("content_type", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="+", to="contenttypes.contenttype")),
                ("shared_with_groups", models.ManyToManyField(blank=True, help_text="Groups with whom this preference is shared.", related_name="shared_%(class)s_preferences", to="auth.group")),
                ("shared_with_users", models.ManyToManyField(blank=True, help_text="Users with whom this preference is shared.", related_name="shared_%(class)s_preferences", to=settings.AUTH_USER_MODEL)),
                ("source_object", models.ForeignKey(blank=True, help_text="Reference to the original preference from which this preference was derived. This is used to track the origin of derived preferences.", null=True, on_delete=django.db.models.deletion.CASCADE, related_name="derived_%(class)s_preferences", to="bloomerp.userdetailviewtabspreference")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="%(class)s_preferences", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "bloomerp_user_detail_view_tabs_preference"},
        ),
        migrations.CreateModel(
            name="UserDetailViewTabItem",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)),
                ("url", models.CharField(blank=True, max_length=2048, null=True)),
                ("position", models.PositiveIntegerField(default=0)),
                ("parent", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="children", to="bloomerp.userdetailviewtabitem")),
                ("preference", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="bloomerp.userdetailviewtabspreference")),
            ],
            options={
                "db_table": "bloomerp_user_detail_view_tab_item",
                "ordering": ["position", "id"],
            },
        ),
        migrations.AddConstraint(
            model_name="userdetailviewtabspreference",
            constraint=models.UniqueConstraint(condition=models.Q(("selected", True)), fields=("user", "content_type"), name="unique_selected_detail_tabs_preference"),
        ),
        migrations.AddConstraint(
            model_name="userdetailviewtabspreference",
            constraint=models.UniqueConstraint(condition=models.Q(("source_object__isnull", False)), fields=("user", "source_object"), name="unique_detail_tabs_preference_reference"),
        ),
        migrations.AddIndex(
            model_name="userdetailviewtabitem",
            index=models.Index(fields=["preference", "parent", "position"], name="detail_tab_tree_order_idx"),
        ),
        migrations.AddConstraint(
            model_name="userdetailviewtabitem",
            constraint=models.CheckConstraint(condition=models.Q(("url__isnull", True), models.Q(("url", ""), _negated=True), _connector="OR"), name="detail_tab_url_null_or_nonempty"),
        ),
    ]
