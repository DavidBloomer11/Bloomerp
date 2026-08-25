from django.utils.translation import gettext_lazy as _
import uuid
from django.conf import settings
from bloomerp.models import BloomerpModel
from bloomerp.models.definition import BloomerpModelConfig
from django.db import models

class AIConversation(BloomerpModel):
    bloomerp_config = BloomerpModelConfig(
        string_search_fields=["title"],
    )

    class Meta:
        managed = True
        db_table = "bloomerp_ai_conversation"
        verbose_name = _("AI conversation")
        verbose_name_plural = _("AI conversations")

    CONVERSATION_TYPES = [
        ('sql', 'SQL'), 
        ('document_template', 'Document Template Generator'), 
        ('tiny_mce_content', 'TinyMCE Content Generator'), 
        ('bloom_ai', 'Bloom AI'),
        ('code', 'Code Generator'),
        ('object_bloom_ai', 'Object Bloom AI')
    ]

    avatar = None
    title = models.CharField(max_length=255, default='AI Conversation', verbose_name=_("Title"))
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name=_("ID"))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("User"))
    conversation_history = models.JSONField(null=True, blank=True, verbose_name=_("Conversation History"))
    conversation_type = models.CharField(max_length=20, choices=CONVERSATION_TYPES, default='bloom_ai', verbose_name=_("Conversation Type"))
    auto_named = models.BooleanField(default=False, help_text="Whether the conversation has been auto-named", verbose_name=_("Auto Named"))
    args = models.JSONField(null=True, blank=True, help_text="Extra arguments for the conversation", verbose_name=_("Args"))

    allow_string_search = False

    @property
    def number_of_messages(self):
        return len(self.conversation_history)
    
    def __str__(self):
        return self.title
    
