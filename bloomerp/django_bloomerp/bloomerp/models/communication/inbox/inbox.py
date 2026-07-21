from bloomerp.models.base_bloomerp_model import BloomerpModel
from django.db import models
from django.conf import settings

from bloomerp.models.communication.inbox.inbox_item import InboxItem

class Inbox(BloomerpModel):
    """
    Represents a user's inbox, which can contain various types of items such as notifications, emails, and internal messages.
    """
    class Meta:
        verbose_name = "Inbox"
    
    owner = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
    )
    name = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        help_text="The name of the inbox, typically associated with the owner."
    )
    members = models.ManyToManyField(
        to=settings.AUTH_USER_MODEL,
        related_name="inbox_members",
        blank=True,
        help_text="Users who have access to this inbox."
    )
    
    
    def get_unread_count(self):
        """
        Returns the count of unread items in the inbox.
        """
        return (
            InboxItem.objects
            .filter(folder__inbox=self, is_read=False)
            .distinct()
            .count()
        )
        
    
    
