from django.utils.translation import gettext_lazy as _
from django.db import models


class TimestampModelMixin(models.Model):
    """
    A mixin for models that need to be timestamped.
    """
    datetime_created = models.DateTimeField(auto_now_add=True, verbose_name=_("Datetime Created"))
    datetime_updated = models.DateTimeField(auto_now=True, verbose_name=_("Datetime Updated"))

    class Meta:
        verbose_name = _("Timestamp Model Mixin")
        verbose_name_plural = _("Timestamp Model Mixins")
        abstract = True