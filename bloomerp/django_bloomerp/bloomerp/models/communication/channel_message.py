from bloomerp.models.base_bloomerp_model import BloomerpModel
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class ChannelMessage(BloomerpModel):
    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        db_table = "bloomerp_channel_message"
    
    avatar = None
    
    content = models.TextField(
        null=True, 
        blank=True,
        help_text="The main content of the message.",
        verbose_name=_("Content")
    )
    
    sender = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
        help_text="The user who sent the message.",
        verbose_name=_("Sender")
    )
    
    parent_message = models.ForeignKey(
        to="self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
        help_text="The parent message if this is a reply.",
        verbose_name=_("Parent Message")
    )
    
    