from django.utils.translation import gettext_lazy as _
from django.db import models
from django.urls import reverse


class AbsoluteUrlModelMixin(models.Model):
    """
    A mixin for models that need to have an absolute URL.
    """
    class Meta:
        verbose_name = _("Absolute URL Model Mixin")
        verbose_name_plural = _("Absolute URL Model Mixins")
        abstract = True

    def get_absolute_url(self):
        """
        Returns the absolute URL of the model instance.
        """
        from bloomerp.utils.models import get_detail_view_url

        return reverse(get_detail_view_url(self.__class__), kwargs={'pk': self.pk})
