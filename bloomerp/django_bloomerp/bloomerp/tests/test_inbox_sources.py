from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from django_celery_beat.models import PeriodicTask

from bloomerp.celery.tasks.email_sync_task import sync_email_account
from bloomerp.communication.emails.base_adapter import BloomerpEmail
from bloomerp.communication.inbox_folder_definition import InboxFolderType
from bloomerp.communication.inbox_sources import (
    InboxEventSource,
    InboxJobSource,
    InboxSourceRegistry,
    execute_registered_source,
    publish_event,
    synchronize_job_schedules,
)
from bloomerp.models.communication.email_account import EmailAccount
from bloomerp.models.communication.inbox.inbox import Inbox
from bloomerp.models.communication.inbox.inbox_folder import InboxFolder
from bloomerp.models.communication.inbox.inbox_item import InboxItem


class InboxSourceRegistryTests(TestCase):
    def test_default_sources_are_discoverable_and_resolve_callables(self):
        """
        Use case: The application loads its built-in inbox sources.
        Expected result: Registered sources expose resolved handlers and resolvers.
        """
        # 1. Resolve the default email job and account event.
        job = InboxSourceRegistry.get_by_key("email.sync.dispatch")
        account_event = InboxSourceRegistry.get_by_key("email.sync.account")

        # 2. Verify their contracts and source types.
        self.assertEqual(job.folder_type, InboxFolderType.EMAIL.value.key)
        self.assertIsInstance(job.source, InboxJobSource)
        self.assertTrue(callable(job.source.resolve_folder_qs_resolver()))
        self.assertTrue(callable(job.source.resolve_handler()))
        self.assertIsInstance(account_event.source, InboxEventSource)

    def test_job_schedule_is_created_from_registered_source(self):
        """
        Use case: Inbox source schedules are synchronized with Celery Beat.
        Expected result: Email polling is registered to run every two minutes.
        """
        # 1. Synchronize source schedules.
        synchronize_job_schedules()

        # 2. Verify the generated Celery Beat task and interval.
        task = PeriodicTask.objects.get(
            name="bloomerp.inbox_source.email.sync.dispatch"
        )
        self.assertEqual(
            task.task,
            "bloomerp.celery.tasks.inbox_source_task.execute_inbox_source_task",
        )
        self.assertEqual(task.args, '["email.sync.dispatch"]')
        self.assertEqual(task.crontab.minute, "*/2")


class EmailInboxSourceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="email-source-user",
            email="email-source-user@example.com",
            password="password",
        )
        self.inbox = Inbox.objects.create(owner=self.user, name="Email inbox")
        self.inbox.members.add(self.user)
        self.email_account = EmailAccount.objects.create(
            name="Support",
            email_address="support-source@example.com",
            status=EmailAccount.Status.ACTIVE,
            sync_enabled=True,
        )
        self.folder = InboxFolder.objects.create(
            inbox=self.inbox,
            type=InboxFolderType.EMAIL.value.key,
            related_object_id=str(self.email_account.id),
        )
        self.notification_folder = InboxFolder.objects.create(
            inbox=self.inbox,
            type=InboxFolderType.IN_APP_NOTIFICATIONS.value.key,
        )

    def _provider_email(self) -> BloomerpEmail:
        return BloomerpEmail(
            provider=self.email_account.provider,
            provider_message_id="provider-message-1",
            email_account_id=str(self.email_account.id),
            mailbox="INBOX",
            subject="Architecture test",
            sender="sender@example.com",
            date=timezone.now(),
            snippet="Inbox source delivery",
        )

    @patch("bloomerp.communication.inbox_sources.send_user_message")
    def test_event_source_resolves_folders_and_forwards_keyword_payload(
        self,
        send_user_message,
    ):
        """
        Use case: A system message event targets a specific user.
        Expected result: The source resolves the folder and forwards its payload.
        """
        # 1. Publish a general system message event.
        deliveries = publish_event(
            "system.message",
            user_ids=[self.user.id],
            system_message_type="general",
            data={"message": "Persistent message", "severity": "info"},
        )

        # 2. Verify persistence in the resolved folder and one broadcast.
        self.assertEqual(len(deliveries), 1)
        item = deliveries[0].items[0]
        self.assertEqual(item.folder, self.notification_folder)
        self.assertEqual(item.snippet, "Persistent message")
        send_user_message.assert_called_once()

    @patch("bloomerp.communication.inbox_sources.send_user_message")
    @patch(
        "bloomerp.communication.emails.actions._fetch_synced_emails_for_account"
    )
    def test_account_source_creates_and_delivers_only_new_items(
        self,
        fetch_synced_emails,
        send_user_message,
    ):
        """
        Use case: The same provider email is returned by consecutive syncs.
        Expected result: Only the first sync creates and broadcasts an inbox item.
        """
        # 1. Return the same provider email for both sync passes.
        fetch_synced_emails.return_value = [self._provider_email()]

        # 2. Execute the registered account source twice.
        first_deliveries = execute_registered_source(
            "email.sync.account",
            email_account_id=str(self.email_account.id),
        )
        second_deliveries = execute_registered_source(
            "email.sync.account",
            email_account_id=str(self.email_account.id),
        )

        # 3. Verify idempotent persistence and delivery.
        self.assertEqual(len(first_deliveries), 1)
        self.assertEqual(len(first_deliveries[0].items), 1)
        self.assertEqual(second_deliveries, ())
        self.assertEqual(InboxItem.objects.filter(folder=self.folder).count(), 1)
        send_user_message.assert_called_once()

    @patch("bloomerp.celery.tasks.email_sync_task.sync_email_account.delay")
    def test_dispatch_source_queues_each_due_account(self, delay):
        """
        Use case: The scheduled email dispatch source runs for a due account.
        Expected result: It delegates that account to the account sync task.
        """
        # 1. Execute the scheduled dispatch source.
        deliveries = execute_registered_source("email.sync.dispatch")

        # 2. Verify asynchronous delegation without a direct item delivery.
        self.assertEqual(deliveries, ())
        delay.assert_called_once_with(str(self.email_account.id))

    @patch("bloomerp.communication.inbox_sources.send_user_message")
    @patch(
        "bloomerp.communication.emails.actions._fetch_synced_emails_for_account"
    )
    def test_account_task_executes_registered_inbox_source(
        self,
        fetch_synced_emails,
        send_user_message,
    ):
        """
        Use case: Celery executes an email account synchronization.
        Expected result: The task delegates to the source and reports its result.
        """
        # 1. Configure the provider response and execute the Celery adapter.
        fetch_synced_emails.return_value = [self._provider_email()]

        result = sync_email_account.run(str(self.email_account.id))

        # 2. Verify the source result and persisted inbox item.
        self.assertEqual(result["status"], "synced")
        self.assertEqual(result["synced_count"], 1)
        self.assertEqual(InboxItem.objects.filter(folder=self.folder).count(), 1)
