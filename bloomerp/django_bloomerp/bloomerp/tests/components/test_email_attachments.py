from email.message import EmailMessage
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from bloomerp.communication.emails.actions import (
    _upsert_email_inbox_item_result,
    render_email,
)
from bloomerp.communication.emails.base_adapter import (
    BloomerpEmail,
    EmailAttachment,
    EmailAttachmentMetadata,
)
from bloomerp.communication.emails.providers.imap_smtp import ImapSmtpAdapter
from bloomerp.communication.inbox_folder_definition import InboxFolderType
from bloomerp.models.communication.email_account import EmailAccount
from bloomerp.models.communication.inbox.inbox import Inbox
from bloomerp.models.communication.inbox.inbox_folder import InboxFolder
from bloomerp.models.communication.inbox.inbox_item import InboxItem


class ImapEmailAttachmentTests(SimpleTestCase):
    def setUp(self):
        self.adapter = ImapSmtpAdapter(SimpleNamespace())
        self.connection = Mock()
        self.connection.select.return_value = ("OK", [b"1"])
        self.adapter.connect = Mock(return_value=self.connection)

    def _message_bytes(self) -> bytes:
        message = EmailMessage()
        message["Subject"] = "Contract"
        message.set_content("Please review the contract.")
        message.add_alternative("<p>Please review the contract.</p>", subtype="html")
        message.add_attachment(
            b"contract content",
            maintype="application",
            subtype="pdf",
            filename="contract.pdf",
        )
        return message.as_bytes()

    def test_synced_email_contains_attachment_metadata(self):
        """
        Use case: An IMAP email contains a regular file attachment.
        Expected result: The synchronized BloomerpEmail contains its attachment metadata.
        """
        # 1. Return a complete MIME message from IMAP.
        self.connection.uid.return_value = (
            "OK",
            [(br"1 (UID 42 FLAGS (\Seen) BODY[])", self._message_bytes())],
        )
        self.adapter.email_account = SimpleNamespace(pk="account-id")

        # 2. Build the provider-neutral synchronized email.
        email = self.adapter._fetch_email_index("42", mailbox="INBOX")

        # 3. Verify the stable MIME-part reference is part of BloomerpEmail metadata.
        self.assertIsNotNone(email)
        self.assertEqual(len(email.attachments), 1)
        self.assertEqual(email.attachments[0].id, "2")
        self.assertEqual(email.attachments[0].filename, "contract.pdf")
        self.assertEqual(email.attachments[0].content_type, "application/pdf")
        self.assertEqual(email.attachments[0].size, len(b"contract content"))
        self.assertEqual(
            email.retrieval_metadata()["attachments"],
            [
                {
                    "id": "2",
                    "filename": "contract.pdf",
                    "content_type": "application/pdf",
                    "size": len(b"contract content"),
                }
            ],
        )

    def test_fetch_email_attachment_resolves_the_referenced_mime_part(self):
        """
        Use case: A user downloads an attachment using its stored MIME-part reference.
        Expected result: The provider returns only the matching attachment payload.
        """
        # 1. Return the same complete MIME message from IMAP.
        self.connection.uid.return_value = (
            "OK",
            [(b"1 (BODY[])", self._message_bytes())],
        )

        # 2. Fetch the attachment by its metadata reference.
        attachment = self.adapter.fetch_email_attachment(
            "42",
            "2",
            mailbox="INBOX",
        )

        # 3. Verify the downloaded filename, type, and bytes.
        self.assertIsNotNone(attachment)
        self.assertEqual(attachment.filename, "contract.pdf")
        self.assertEqual(attachment.content_type, "application/pdf")
        self.assertEqual(attachment.content, b"contract content")


class EmailAttachmentComponentTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="attachment-owner",
            email="attachment-owner@example.com",
            password="password",
        )
        self.other_user = get_user_model().objects.create_user(
            username="attachment-outsider",
            email="attachment-outsider@example.com",
            password="password",
        )
        inbox = Inbox.objects.create(owner=self.user, name="Email inbox")
        self.email_account = EmailAccount.objects.create(
            email_address="attachments@example.com",
        )
        self.folder = InboxFolder.objects.create(
            inbox=inbox,
            type=InboxFolderType.EMAIL.value.key,
            related_object_id=str(self.email_account.pk),
        )
        self.item = InboxItem.objects.create(
            folder=self.folder,
            item_type=InboxFolderType.EMAIL.value.item_type.key,
            related_item_id="message-42",
            title="Contract",
            raw_meta_data={
                "email_account_id": str(self.email_account.pk),
                "provider_message_id": "42",
                "mailbox": "INBOX",
                "attachments": [
                    {
                        "id": "2",
                        "filename": "contract.pdf",
                        "content_type": "application/pdf",
                        "size": 2048,
                    }
                ],
            },
        )

    def test_email_upsert_persists_bloomerp_email_attachments(self):
        """
        Use case: A synchronized BloomerpEmail contains attachment metadata.
        Expected result: Its InboxItem raw metadata contains the same attachments.
        """
        # 1. Build the complete provider-neutral email returned by synchronization.
        email = BloomerpEmail(
            provider="imap",
            provider_message_id="43",
            email_account_id=str(self.email_account.pk),
            subject="Invoice",
            attachments=[
                EmailAttachmentMetadata(
                    id="2",
                    filename="invoice.pdf",
                    content_type="application/pdf",
                    size=4096,
                )
            ],
        )

        # 2. Persist the email through the normal inbox upsert path.
        item, created = _upsert_email_inbox_item_result(email, self.folder)

        # 3. Verify no attachment metadata was lost during persistence.
        self.assertTrue(created)
        self.assertEqual(
            item.raw_meta_data["attachments"],
            [
                {
                    "id": "2",
                    "filename": "invoice.pdf",
                    "content_type": "application/pdf",
                    "size": 4096,
                }
            ],
        )

    @patch(
        "bloomerp.communication.emails.actions."
        "_resolve_email_adapter_for_account"
    )
    def test_render_email_uses_stored_metadata_for_attachment_card(
        self,
        resolve_adapter,
    ):
        """
        Use case: A user opens a synchronized email containing attachment metadata.
        Expected result: The stored metadata renders an Outlook-style download card.
        """
        # 1. Return only the provider-backed email body.
        resolve_adapter.return_value.fetch_email_content.return_value = (
            "<p>Email body</p>"
        )

        # 2. Render the email fragment.
        request = RequestFactory().get("/inbox/")
        html = render_email(self.item, request)

        # 3. Verify the attachment presentation uses the synchronized metadata.
        self.assertIn("contract.pdf", html)
        self.assertIn("2.0\xa0KB", html)
        self.assertIn("components/communication/emails/download_attachment", html)
        self.assertIn("rounded-xl border border-gray-200", html)
        self.assertIn("<iframe", html)
        self.assertIn('sandbox="allow-popups allow-popups-to-escape-sandbox"', html)
        self.assertNotIn("<style>", html)

    @patch(
        "bloomerp.components.communication.emails.download_attachment."
        "fetch_email_attachment"
    )
    def test_inbox_owner_can_download_attachment(self, fetch_attachment):
        """
        Use case: The inbox owner downloads an attachment referenced by an email item.
        Expected result: The component streams the file with safe response headers.
        """
        # 1. Configure the provider-backed attachment response.
        fetch_attachment.return_value = EmailAttachment(
            filename="contract.pdf",
            content=b"contract content",
            content_type="application/pdf",
        )
        self.client.force_login(self.user)

        # 2. Request the attachment through the secured component.
        response = self.client.get(
            reverse(
                "components_emails_download_attachment",
                kwargs={
                    "inbox_item_id": self.item.pk,
                    "attachment_id": "2",
                },
            )
        )

        # 3. Verify the streamed file and download headers.
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"contract content")
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("contract.pdf", response["Content-Disposition"])
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")

    @patch(
        "bloomerp.components.communication.emails.download_attachment."
        "fetch_email_attachment"
    )
    def test_user_outside_inbox_cannot_download_attachment(self, fetch_attachment):
        """
        Use case: A signed-in user requests an attachment from somebody else's inbox.
        Expected result: The component returns not found without contacting the provider.
        """
        # 1. Sign in as a user who is neither the inbox owner nor a member.
        self.client.force_login(self.other_user)

        # 2. Request the private attachment.
        response = self.client.get(
            reverse(
                "components_emails_download_attachment",
                kwargs={
                    "inbox_item_id": self.item.pk,
                    "attachment_id": "2",
                },
            )
        )

        # 3. Verify access is denied before provider retrieval.
        self.assertEqual(response.status_code, 404)
        fetch_attachment.assert_not_called()
