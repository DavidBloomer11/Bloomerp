from django.utils.translation import gettext_lazy as _
import uuid

from django.db import models


class UuidModelMixin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name=_("ID"))

    class Meta:
        verbose_name = _("UUID Model Mixin")
        verbose_name_plural = _("UUID Model Mixins")
        abstract = True
