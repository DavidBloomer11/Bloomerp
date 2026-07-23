from django.contrib.contenttypes.models import ContentType
from bloomerp.models.mixins.content_layout_model_mixin import ContentLayoutModelMixin
from bloomerp.models.users.base_view_preference import BaseViewPreference


class UserObjectLayoutPreference(ContentLayoutModelMixin, BaseViewPreference):
    """Model to store user preferences for object layouts."""

    class Meta:
        verbose_name = "User Object Layout Preference"
        verbose_name_plural = "User Object Layout Preferences"

    @classmethod
    def create_default_for_user(cls, user, **scope) -> "UserObjectLayoutPreference":
        """Create a permission-neutral layout shared by create and detail views."""
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

    @classmethod
    def copy_preference_for_user(
        cls,
        *,
        user,
        source: "UserObjectLayoutPreference",
        name: str,
        scope: dict | None = None,
    ) -> "UserObjectLayoutPreference":
        """Copy an object-layout preference."""
        return cls._create_preference_copy(
            user=user,
            source=source,
            name=name,
            scope=scope,
        )

    def ensure_default_state(self, *, user, content_type: ContentType) -> None:
        if self.layout_obj.rows and any(row.items for row in self.layout_obj.rows):
            return

        from bloomerp.services.sectioned_layout_services import create_default_layout

        model = content_type.model_class()
        if model is None:
            return
        self.layout = create_default_layout(model).model_dump()
        self.save(update_fields=["layout"])
