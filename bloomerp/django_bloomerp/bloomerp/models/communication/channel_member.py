from bloomerp.models import BloomerpModel
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class ChannelMember(BloomerpModel):
    class Meta:
        verbose_name = _("Channel Member")
        verbose_name_plural = _("Channel Members")
        db_table = "bloomerp_channel_member"
        
        constraints = [
            models.UniqueConstraint(
                fields=["channel", "user"],
                name="unique_channel_membership",
            ),
        ]
    
    class Role(models.TextChoices):
        MEMBER = "member", _("Member")
        ADMIN = "admin", _("Admin")
        OWNER = "owner", _("Owner")

    avatar = None
    
    channel = models.ForeignKey(
        "Channel",
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name=_("Channel"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="channel_memberships",
        verbose_name=_("User"),
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
        verbose_name=_("Role"),
    )

    last_read_message = models.ForeignKey(
        "ChannelMessage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("Last Read Message"),
    )
    muted_until = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name=_("Muted Until")
    )

        
    @property
    def joined_at(self) -> models.DateTimeField:
        """Returns a timestamp of when the user joined

        Returns:
            models.DateTimeField: The timestamp of when the user joined the channel.
        """
        return self.datetime_created
