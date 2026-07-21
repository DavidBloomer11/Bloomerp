from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q

from bloomerp.models.base_bloomerp_model import BloomerpModel
from bloomerp.models.mixins.content_layout_model_mixin import ContentLayoutModelMixin
from bloomerp.models.users.base_view_preference import BaseViewPreference
from bloomerp.models.users.user import AbstractBloomerpUser

class UserCreateViewPreference(ContentLayoutModelMixin, BaseViewPreference):
    """
    Stores the create-view field layout preference per user and content type.
    """
    class Meta(BloomerpModel.Meta):
        managed = True
        db_table = "bloomerp_user_create_view_preference"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "content_type"],
                condition=Q(selected=True),
                name="unique_selected_create_view_preference",
            ),
            models.UniqueConstraint(
                fields=["user", "source_object"],
                condition=Q(source_object__isnull=False),
                name="unique_create_view_preference_reference",
            ),
        ]
    @classmethod
    def create_default_for_user(
        cls,
        user: AbstractBloomerpUser,
        **scope,
    ) -> "UserCreateViewPreference":
        """Create the user's default create-view preference for a content type.

        Expected scope: ``content_type_id``.
        """
        from bloomerp.services.sectioned_layout_services import create_default_layout

        content_type = ContentType.objects.get(pk=scope["content_type_id"])
        model = content_type.model_class()
        if model is None:
            raise ValueError("The content type does not resolve to a model.")
        return cls.objects.create(
            user=user,
            content_type=content_type,
            layout=create_default_layout(model).model_dump(),
        )

    def ensure_default_state(self, *, user, content_type: ContentType) -> None:
        if not self.layout_obj.rows or not any(row.items for row in self.layout_obj.rows):
            from bloomerp.services.sectioned_layout_services import create_default_layout

            model = content_type.model_class()
            if model is None:
                return
            self.layout = create_default_layout(model).model_dump()
            self.save(update_fields=["layout"])
