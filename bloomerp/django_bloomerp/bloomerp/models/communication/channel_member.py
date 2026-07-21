from bloomerp.models.base_bloomerp_model import BloomerpModel
from django.db import models
from django.conf import settings

class ChannelMember(BloomerpModel):
    class Meta:
        verbose_name = "Channel Member"
        verbose_name_plural = "Channel Members"
        db_table = "bloomerp_channel_member"
        
        constraints = [
            models.UniqueConstraint(
                fields=["channel", "user"],
                name="unique_channel_membership",
            ),
        ]
    
    class Role(models.TextChoices):
        MEMBER = "member", "Member"
        ADMIN = "admin", "Admin"
        OWNER = "owner", "Owner"

    avatar = None
    
    channel = models.ForeignKey(
        "Channel",
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="channel_memberships",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
    )

    last_read_message = models.ForeignKey(
        "ChannelMessage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    muted_until = models.DateTimeField(
        null=True, 
        blank=True
    )

        
    @property
    def joined_at(self) -> models.DateTimeField:
        """Returns a timestamp of when the user joined

        Returns:
            models.DateTimeField: The timestamp of when the user joined the channel.
        """
        return self.datetime_created