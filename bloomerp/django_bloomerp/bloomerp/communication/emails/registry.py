"""
Registry for BloomERP email providers.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Type

from django.template.loader import render_to_string

from bloomerp.communication.emails.base_adapter import BaseEmailAdapter
from bloomerp.communication.emails.providers.imap_smtp import ImapSmtpAdapter
from bloomerp.utils.registry import BaseRegistry


class EmailSyncMode(Enum):
	POLLING = "polling"
	PUSH = "push"

	@property
	def label(self) -> str:
		return self.value.title()


@dataclass(frozen=True)
class EmailSyncCapability:
	default_mode: EmailSyncMode = EmailSyncMode.POLLING
	default_poll_interval_minutes: int = 5
	supported_modes: list[EmailSyncMode] = field(
		default_factory=lambda: [EmailSyncMode.POLLING]
	)


@dataclass(frozen=True)
class EmailProviderDefinition:
	key: str
	name: str
	description: str
	icon: str
	adapter_class: Type[BaseEmailAdapter]
	fields: list[str] = field(default_factory=list)
	required_fields: list[str] = field(default_factory=list)
	initial: dict[str, Any] = field(default_factory=dict)
	setup_instructions: str | None = None
	sync_capabilities: EmailSyncCapability = field(default_factory=EmailSyncCapability)


class EmailProviderRegistry(BaseRegistry[EmailProviderDefinition]):
	pass


EMAIL_PROVIDER_REGISTRY = EmailProviderRegistry(EmailProviderDefinition)

EMAIL_PROVIDER_REGISTRY.register(
	"IMAP",
	EmailProviderDefinition(
		key="imap",
		name="IMAP / SMTP",
		description="Connect a mailbox with incoming and outgoing server credentials.",
		icon="fa-solid fa-envelope-open-text",
		adapter_class=ImapSmtpAdapter,
		fields=[
			"name",
			"email_address",
			"username",
			"password",
			"imap_host",
			"imap_port",
			"imap_security",
			"smtp_host",
			"smtp_port",
			"smtp_security",
		],
		required_fields=[
			"email_address",
			"imap_host",
			"imap_port",
			"smtp_host",
			"smtp_port",
		],
		setup_instructions=render_to_string(
			"models/email_account/provider_instructions/imap.html"
		),
		sync_capabilities=EmailSyncCapability(
			default_mode=EmailSyncMode.POLLING,
			supported_modes=[EmailSyncMode.POLLING],
			default_poll_interval_minutes=5,
		),
	),
)