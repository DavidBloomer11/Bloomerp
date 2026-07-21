import datetime
import imaplib
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from bloomerp.communication.emails.providers.imap_smtp import ImapSmtpAdapter
from bloomerp.communication.emails.sync import handle_email_account_sync
from bloomerp.components.communication.emails.sync_emails import SyncEmailsForm


class SyncEmailsFormTests(SimpleTestCase):
    def test_all_mailboxes_are_selected_initially(self):
        mailboxes = ["INBOX", "[Gmail]/Sent Mail"]

        form = SyncEmailsForm(mailboxes=mailboxes)

        self.assertEqual(form["mailboxes"].value(), mailboxes)

    def test_bound_form_preserves_an_empty_mailbox_selection(self):
        form = SyncEmailsForm(
            data={},
            mailboxes=["INBOX", "[Gmail]/Sent Mail"],
        )

        self.assertIsNone(form["mailboxes"].value())
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["mailboxes"], [])


class ImapMailboxDiscoveryTests(SimpleTestCase):
    def test_list_mailboxes_excludes_noselect_hierarchy_containers(self):
        adapter = ImapSmtpAdapter(SimpleNamespace())
        connection = Mock()
        connection.list.return_value = (
            "OK",
            [
                br'(\HasNoChildren) "/" "INBOX"',
                br'(\HasChildren \Noselect) "/" "[Gmail]"',
                br'(\HasNoChildren) "/" "[Gmail]/Sent Mail"',
            ],
        )
        adapter.connect = Mock(return_value=connection)

        self.assertEqual(
            adapter.list_mailboxes(),
            ["INBOX", "[Gmail]/Sent Mail"],
        )

    def test_select_mailbox_quotes_names_containing_spaces(self):
        adapter = ImapSmtpAdapter(SimpleNamespace())
        connection = Mock()
        connection.select.return_value = ("OK", [b"1"])
        adapter.connect = Mock(return_value=connection)

        adapter._select_mailbox("[Gmail]/All Mail", readonly=True)

        connection.select.assert_called_once_with(
            '"[Gmail]/All Mail"',
            readonly=True,
        )

    def test_select_mailbox_converts_imap_errors_to_validation_errors(self):
        adapter = ImapSmtpAdapter(SimpleNamespace())
        connection = Mock()
        connection.select.side_effect = imaplib.IMAP4.error(
            "EXAMINE command error"
        )
        adapter.connect = Mock(return_value=connection)

        with self.assertRaisesMessage(
            ValidationError,
            "Unable to select mailbox [Gmail]/All Mail",
        ):
            adapter._select_mailbox("[Gmail]/All Mail", readonly=True)


class EmailSyncSourceTests(SimpleTestCase):
    @patch("bloomerp.communication.emails.sync.EmailAccount.objects.get")
    @patch("bloomerp.communication.emails.actions._upsert_new_emails_to_folder")
    @patch("bloomerp.communication.emails.actions._fetch_synced_emails_for_account")
    def test_account_sync_forwards_action_filters(
        self,
        fetch_synced_emails,
        upsert_new_emails,
        get_email_account,
    ):
        email_account = SimpleNamespace(mailboxes=["INBOX"])
        folder = object()
        start_date = datetime.date(2026, 7, 1)
        end_date = datetime.date(2026, 7, 21)
        get_email_account.return_value = email_account
        fetch_synced_emails.return_value = []
        upsert_new_emails.return_value = ()

        handle_email_account_sync(
            [folder],
            email_account_id="account-id",
            from_date=start_date,
            to_date=end_date,
            limit=25,
            mailboxes=["INBOX"],
        )

        fetch_synced_emails.assert_called_once_with(
            email_account,
            from_date=start_date,
            to_date=end_date,
            limit=25,
            mailbox="INBOX",
        )
