import imaplib
import email
from email.header import decode_header
from dataclasses import dataclass


@dataclass
class EmailSummary:
    uid: str
    subject: str
    sender: str
    date: str


def decode_mime_header(value: str | None) -> str:
    if not value:
        return ""

    parts = decode_header(value)
    decoded = []

    for part, encoding in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(encoding or "utf-8", errors="replace"))
        else:
            decoded.append(part)

    return "".join(decoded)


def fetch_first_50_emails(
    username: str,
    app_password: str,
    mailbox: str = "INBOX",
    search_criteria: str | tuple[str, ...] = "ALL",
) -> list[EmailSummary]:
    client = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    normalized_username = username.strip()
    normalized_app_password = "".join(app_password.split())
    criteria = (search_criteria,) if isinstance(search_criteria, str) else search_criteria

    try:
        client.login(normalized_username, normalized_app_password)
        status, _ = client.select(mailbox, readonly=True)

        if status != "OK":
            raise RuntimeError(f"Could not select mailbox: {mailbox}")

        # Examples: "ALL", "UNSEEN", or ("FROM", '"name@example.com"').
        status, data = client.uid("search", None, *criteria)

        if status != "OK":
            raise RuntimeError("Could not search mailbox")

        uids = data[0].split()

        # IMAP ordering is oldest -> newest: first 50 emails.
        first_50_uids = uids[:50]

        emails = []

        for uid in first_50_uids:
            status, message_data = client.uid(
                "fetch",
                uid,
                "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])",
            )

            if status != "OK":
                continue

            raw_headers = message_data[0][1]
            message = email.message_from_bytes(raw_headers)

            emails.append(
                EmailSummary(
                    uid=uid.decode(),
                    subject=decode_mime_header(message.get("Subject")),
                    sender=decode_mime_header(message.get("From")),
                    date=message.get("Date", ""),
                )
            )

        return emails

    finally:
        client.logout()


emails = fetch_first_50_emails(
    username="bloomerdavid11@gmail.com",
    app_password="pcnc qzjo mobq ysdj",
    search_criteria="ALL",
)

for item in emails:
    print(item)