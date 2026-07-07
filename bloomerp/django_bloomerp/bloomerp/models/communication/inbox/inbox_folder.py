from typing import Type

from django.db import models
from bloomerp.communication.inbox_folder_definition import InboxFolderType, InboxFolderTypeDefinition
from bloomerp.models.base_bloomerp_model import BloomerpModel
from bloomerp.models.communication.inbox.inbox_item import InboxItem
from bloomerp.utils.requests import parse_bool_parameter
from django.db.models.query import QuerySet

class InboxFolder(BloomerpModel):
    class Meta:
        verbose_name = "Inbox Folder"
        verbose_name_plural = "Inbox Folders"
        db_table = "bloomerp_inbox_folder"
    
    inbox = models.ForeignKey(
        "Inbox",
        on_delete=models.CASCADE,
        related_name="folders",
    )
    type = models.CharField(
        max_length=50,
        choices=InboxFolderType.choices()
    )
    related_object_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    
    @property
    def name(self) -> str:
        """
        Returns a human-readable name for the folder based on its type.
        """
        if self.related_object():
            return str(self.related_object())
        return self.inbox_folder_type().name
    
    @property
    def icon(self) -> str:
        """
        Returns the icon associated with the folder's type.
        """
        return self.inbox_folder_type().icon
    
    def related_object(self) -> models.Model | None:
        """
        Returns the related object for the folder, if any.
        """
        source_model = self.related_model()
        if not source_model or not self.related_object_id:
            return None
        
        try:
            return source_model.objects.get(pk=self.related_object_id)
        except source_model.DoesNotExist:
            return None
    
    def related_model(self) -> Type[models.Model] | None:
        """
        Returns the model class associated with the folder's type.
        """
        return self.inbox_folder_type().get_source_model_class()
    
    def inbox_folder_type(self) -> InboxFolderTypeDefinition:
        """
        Returns the InboxFolderType enum value corresponding to the folder's type.
        """
        return InboxFolderType.from_key(self.type).value
    
    def query_items(self, query_params: dict) -> QuerySet[InboxItem]:
        """
        Queries the items in the folder based on the provided query parameters.
        """
        deep_search = (
            parse_bool_parameter(query_params.get("deep_query"))
            or parse_bool_parameter(query_params.get("deep_search"))
        )
        
        folder_type = self.inbox_folder_type()
        return folder_type.on_query(
            query_params,
            self,
            deep_search
        )
        
        
    def __str__(self) -> str:
        """
        Returns a string representation of the folder.
        """
        return f"{self.name} ({self.type})"
