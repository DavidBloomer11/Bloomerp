from django.utils.translation import gettext_lazy as _
from bloomerp.model_fields.user_field import UserField


from django.db import models


class UserStampModelMixin(models.Model):
    """
    A mixin for models that need to be stamped with the user that created or updated them.
    """
    class Meta:
        abstract = True
            
    created_by = UserField(
        on_delete=models.SET_NULL,
        related_name='%(class)s_created',
        null=True,
        blank=True,
        verbose_name=_("Created By"),
        )
    updated_by = UserField(
        on_delete=models.SET_NULL,
        related_name='%(class)s_updated',
        null=True,
        blank=True,
        verbose_name=_("Updated By"),
        )

    