from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.http import HttpRequest
from django.urls import reverse
from bloomerp.models import BloomerpModel
from bloomerp.models.definition import (
    BloomerpModelConfig,
    ObjectModalAction,
    StringSearchSettings,
)
from bloomerp.models.mixins.absolute_url_model_mixin import AbsoluteUrlModelMixin
from bloomerp.models.mixins.timestamp_model_mixin import TimestampModelMixin
from bloomerp.models.mixins.user_stamp_model_mixin import UserStampModelMixin
from bloomerp.permissions.definition import BloomerpPermission
from bloomerp.permissions.manager import UserPolicyManager
from django.utils.translation import gettext_noop


def user_can_change_folder(request: HttpRequest, folder: "FileFolder") -> bool:
    return not folder.protected and UserPolicyManager(
        request.user
    ).has_global_permission(type(folder), BloomerpPermission.CHANGE)


def user_can_delete_folder(request: HttpRequest, folder: "FileFolder") -> bool:
    return not folder.protected and UserPolicyManager(
        request.user
    ).has_global_permission(type(folder), BloomerpPermission.DELETE)


class FileFolder(
    TimestampModelMixin,
    UserStampModelMixin,
    AbsoluteUrlModelMixin,
    models.Model,
):
    bloomerp_config = BloomerpModelConfig(
        string_search_settings=StringSearchSettings(
            string_search_fields=["name"],
            allow_global_search=False,
        ),
        object_actions=[
            ObjectModalAction(
                id="rename_folder",
                label=gettext_noop("Rename"),
                endpoint=lambda folder: reverse(
                    "components_files_rename_folder",
                    kwargs={"folder_id": folder.pk},
                ),
                should_render_func=user_can_change_folder,
                modal_title=gettext_noop("Rename folder"),
            ),
            ObjectModalAction(
                id="delete_folder",
                label=gettext_noop("Delete"),
                endpoint=lambda folder: reverse(
                    "components_files_delete_folder",
                    kwargs={"folder_id": folder.pk},
                ),
                should_render_func=user_can_delete_folder,
                modal_title=gettext_noop("Delete folder"),
                style="secondary",
            ),
        ],
    )

    class Meta(BloomerpModel.Meta):
        verbose_name = _("File Folder")
        verbose_name_plural = _("File Folders")
        managed = True
        db_table = "bloomerp_file_folder"

    name = models.CharField(max_length=255, verbose_name=_("Name"))
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Parent"))
    content_type = models.ForeignKey(
        to=ContentType, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name=_("Content Type"),
    )
    object_id = models.CharField(
        max_length=36, 
        null=True, 
        blank=True,
        verbose_name=_("Object ID"),
        )
    content_object = GenericForeignKey(
        ct_field="content_type", 
        fk_field="object_id"
        )
    protected = models.BooleanField(
        default=False,
        help_text="Protected folders cannot be edited or deleted through the UI. This is useful for folders that are automatically created for objects, such as the module-level folders created for files.",
        verbose_name=_("Protected"),
        )


    def __str__(self):
        return self.name


    def clean(self):
        super().clean()

        if self.object_id and not self.content_type_id:
            raise ValidationError({"content_type": "content_type is required when object_id is set."})

        if not self.parent_id:
            return

        parent = self.parent
        if parent is None:
            return

        if parent.content_type_id and self.content_type_id != parent.content_type_id:
            raise ValidationError(
                {"content_type": "Child folders must inherit the parent's content_type."}
            )

        if (parent.object_id or None) and (self.object_id or None) != (parent.object_id or None):
            raise ValidationError(
                {"object_id": "Child folders must inherit the parent's object_id."}
            )

    def save(self, *args, **kwargs):
        self.full_clean(exclude=["created_by", "updated_by"])
        return super().save(*args, **kwargs)

    @property
    def parents(self):
        """Returns a list of parent folders."""
        parents = []
        parent = self.parent
        while parent:
            parents.append(parent)
            parent = parent.parent

        # Reverse the list to get the parents in the correct order
        return list(reversed(parents))
    
    @property
    def children(self):
        """Returns a list of child folders."""
        return FileFolder.objects.filter(parent=self)
