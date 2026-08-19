from django.utils.translation import gettext_lazy as _
from django.db import models


class AvatarModelMixin(models.Model):
    """
    A mixin for models that need to have an avatar.
    """
    class Meta:
        verbose_name = _("Avatar Model Mixin")
        verbose_name_plural = _("Avatar Model Mixins")
        abstract = True
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name=_("Avatar"))