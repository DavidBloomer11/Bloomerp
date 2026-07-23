from bloomerp.models.base_bloomerp_model import BloomerpModel
from bloomerp.models.definition import BloomerpModelConfig
from bloomerp.models.users.user import AbstractBloomerpUser
from django.db import models
from django.conf import settings


class UserInboxPreference(BloomerpModel):
    class Meta:
        verbose_name = "User Inbox Preference"
        verbose_name_plural = "User Inbox Preferences"

    bloomerp_config = BloomerpModelConfig(
        record_activity_log=False,
        is_internal=True,
    )

    user = models.OneToOneField(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="inbox_preference",
    )
    selected_inbox_folder = models.ForeignKey(
        to="InboxFolder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users_with_selected_inbox_folder_preference",
    )

    @classmethod
    def get_for_user(cls, user: AbstractBloomerpUser) -> "UserInboxPreference":
        preference, _ = cls.objects.get_or_create(user=user)
        return preference
