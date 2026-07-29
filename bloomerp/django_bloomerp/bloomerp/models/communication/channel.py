from django.db import models
from bloomerp.models.base_bloomerp_model import BloomerpModel



class Channel(BloomerpModel):
    class Meta:
        verbose_name = "Channel"
        verbose_name_plural = "Channels"
        db_table = "bloomerp_channel"
    
    # Type related fields
    channel_type = models.CharField(
        max_length=255, 
        null=False, 
        blank=False
    )
    
    # Content related fields
    is_active = models.BooleanField(
        default=True,
        help_text="Indicates whether the channel is currently active."
    )