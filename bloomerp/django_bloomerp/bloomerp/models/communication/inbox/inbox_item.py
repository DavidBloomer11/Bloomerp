from typing import Type

from django.db import models
from django.db.models import Q
from django.http import HttpRequest
from bloomerp.communication.inbox_folder_definition import InboxItemTypeDefinition, InboxFolderType
from bloomerp.models.base_bloomerp_model import BloomerpModel
from bloomerp.models.definition import BloomerpModelConfig

class InboxItem(BloomerpModel):
    class Meta:
        verbose_name = "Inbox Item"
        verbose_name_plural = "Inbox Items"
        db_table = "bloomerp_inbox_item"
        constraints = [
            models.UniqueConstraint(
                fields=["folder", "item_type", "related_item_id"],
                condition=Q(
                    item_type="email",
                    related_item_id__isnull=False,
                ),
                name="uniq_email_item_identity",
            ),
        ]
    
    bloomerp_config = BloomerpModelConfig(
        record_activity_log=False,
    )
    
    item_type = models.CharField(
        max_length=50,
        choices=[(i.value.item_type.key, i.value.item_type.name) for i in InboxFolderType if isinstance(i.value.item_type, InboxItemTypeDefinition)],
    )
    
    # Type related fields
    related_item_id = models.CharField(
        max_length=1000,
        null=True, 
        blank=True,
        help_text="Optional reference to the source item's ID, if applicable."
    )
    
    # Rel with folder
    folder = models.ForeignKey(
        to="InboxFolder",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="inbox_items",
        help_text="The folder to which this inbox item belongs.",
    )
    
    # Content related fields
    actor = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="The actor or entity associated with the inbox item."
    )
    
    is_read = models.BooleanField(
        default=False,
        help_text="Indicates whether the inbox item has been read by the user."
    )
    datetime_received = models.DateTimeField(
        null=True,
        blank=True,
        editable=False,
        db_index=True,
        help_text="Timestamp when the inbox item was received by its source system.",
    )
    
    title = models.CharField(
        max_length=1000,
        null=False,
        blank=False,
        help_text="The title of the inbox item."
    )
    
    snippet = models.TextField(
        null=True,
        blank=True,
        help_text="A brief snippet or summary of the inbox item content."
    )
    
    raw_meta_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Optional JSON field to store additional metadata related to the inbox item."
    )
    
    @property
    def source_model(self) -> Type[models.Model] | None:
        pass
    
    def get_inbox_item_type(self) -> InboxItemTypeDefinition | None:
        """
        Retrieves the InboxItemTypeDefinition associated with this inbox item.

        Returns:
            InboxItemTypeDefinition: The definition of the inbox item type.
        """
        return InboxFolderType.get_item_type_by_key(self.item_type)
    
    @property
    def icon(self) -> str:
        """
        Returns the icon associated with the inbox item type.

        Returns:
            str: The icon string for the inbox item type.
        """
        item_type_def = self.get_inbox_item_type()
        return item_type_def.icon if item_type_def else ""
    
    
    def render(self, request:HttpRequest) -> str:
        """
        Renders the inbox item content based on its type.

        Returns:
            str: The rendered content of the inbox item.
        """
        return self.get_inbox_item_type().on_render(
            self, request
        ) if self.get_inbox_item_type() else ""

    def save(self, *args, **kwargs):
        should_backfill_received = self.datetime_received is None
        super().save(*args, **kwargs)
        if should_backfill_received and self.datetime_created:
            self.datetime_received = self.datetime_created
            type(self).objects.filter(pk=self.pk, datetime_received__isnull=True).update(
                datetime_received=self.datetime_created
            )
