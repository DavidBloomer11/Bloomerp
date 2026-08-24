from django.db import models
from bloomerp.models.base_bloomerp_model import BloomerpModel
from django.utils.translation import gettext_lazy as _


class Channel(BloomerpModel):
    class Meta:
        verbose_name = _("Channel")
        verbose_name_plural = _("Channels")
        db_table = "bloomerp_channel"
    
    # Type related fields
    channel_type = models.CharField(
        max_length=255, 
        null=False, 
        blank=False,
        verbose_name=_("Channel Type")
    )
    
    # Content related fields
    is_active = models.BooleanField(
        default=True,
        help_text=_("Indicates whether the channel is currently active."),
        verbose_name=_("Is Active")
    )