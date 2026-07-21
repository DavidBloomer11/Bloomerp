from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from django.http import HttpRequest

from bloomerp.utils.base_type_definition import BaseTypeDefinition

if TYPE_CHECKING:
    from bloomerp.models.communication.inbox.inbox_folder import InboxFolder
    from bloomerp.models.communication.inbox.inbox_item import InboxItem


SYSTEM_MESSAGE_ACTOR = "System"


@dataclass(frozen=True, kw_only=True)
class SystemMessageItemData:
    """Validated, durable fields produced by one system-message type."""

    title: str
    snippet: str = ""
    related_item_id: str | None = None
    raw_meta_data: dict = field(default_factory=dict)


class BaseSystemMessageType(ABC):
    @classmethod
    @abstractmethod
    def build_item_data(cls, data: dict) -> SystemMessageItemData:
        """Turn source data into fields that remain useful after source deletion."""

    @classmethod
    @abstractmethod
    def render(
        cls,
        item: "InboxItem",
        request: HttpRequest | None = None,
    ) -> str:
        """Render the persisted system-message snapshot."""


@dataclass(frozen=True)
class SystemMessageDefinition:
    key: str
    name: str
    cls: type[BaseSystemMessageType]


# Import concrete implementations only after the base contract is defined.
from bloomerp.communication.system_messages.general import GeneralSystemMessage  # noqa: E402
from bloomerp.communication.system_messages.workflow import WorkflowSystemMessage  # noqa: E402


class SystemMessage(BaseTypeDefinition):
    GENERAL = SystemMessageDefinition(
        key="general",
        name="General",
        cls=GeneralSystemMessage,
    )
    WORKFLOW = SystemMessageDefinition(
        key="workflow",
        name="Workflow",
        cls=WorkflowSystemMessage,
    )

    @classmethod
    def get_definition(cls, message_type: str) -> SystemMessageDefinition:
        resolved = cls.from_key(message_type)
        if resolved is None:
            raise ValueError(f"Invalid system message type: {message_type!r}")
        return resolved.value

    @classmethod
    def resolve_render(
        cls,
        item: "InboxItem",
        request: HttpRequest | None = None,
    ) -> str:
        raw_meta_data = item.raw_meta_data or {}
        message_type = raw_meta_data.get("system_message_type") or "general"
        definition = cls.from_key(message_type) or cls.GENERAL
        return definition.value.cls.render(item, request=request)

    @classmethod
    def create_item(
        cls,
        *,
        message_type: str,
        folder: "InboxFolder",
        data: dict,
    ) -> "InboxItem":
        from bloomerp.communication.inbox_folder_definition import InboxFolderType
        from bloomerp.models.communication.inbox.inbox_item import InboxItem

        definition = cls.get_definition(message_type)
        item_data = definition.cls.build_item_data(data)
        raw_meta_data = {
            **item_data.raw_meta_data,
            "system_message_type": definition.key,
        }

        return InboxItem.objects.create(
            folder=folder,
            item_type=InboxFolderType.IN_APP_NOTIFICATIONS.value.item_type.key,
            actor=SYSTEM_MESSAGE_ACTOR,
            title=item_data.title,
            snippet=item_data.snippet,
            related_item_id=item_data.related_item_id,
            raw_meta_data=raw_meta_data,
        )
