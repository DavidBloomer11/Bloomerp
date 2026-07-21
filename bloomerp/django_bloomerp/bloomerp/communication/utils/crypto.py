from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.utils.crypto import salted_hmac
import base64


def _get_email_secret_key() -> str:
    bloomerp_config = getattr(settings, "BLOOMERP_CONFIG", None)
    secret_key = getattr(bloomerp_config, "email_secret_key", None)
    if not secret_key:
        raise ImproperlyConfigured("BLOOMERP_CONFIG.email_secret_key must be set to store email account secrets.")
    return str(secret_key)


def _get_fernet() -> Fernet:
    digest = salted_hmac(
        key_salt="bloomerp.emails.crypto",
        value="email-account-secret-v1",
        secret=_get_email_secret_key(),
        algorithm="sha256",
    ).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


ENCRYPTED_SECRET_PREFIX = "blpenc:v1:"


def is_encrypted_email_secret(value: str | None) -> bool:
    return bool(value and str(value).startswith(ENCRYPTED_SECRET_PREFIX))


def encrypt_email_secret(value: str | None) -> str:
    if value in (None, ""):
        return ""

    value = str(value)
    if is_encrypted_email_secret(value):
        return value

    token = _get_fernet().encrypt(value.encode("utf-8")).decode("ascii")
    return f"{ENCRYPTED_SECRET_PREFIX}{token}"


def decrypt_email_secret(value: str | None) -> str:
    if value in (None, ""):
        return ""

    value = str(value)
    if not is_encrypted_email_secret(value):
        return value

    token = value.removeprefix(ENCRYPTED_SECRET_PREFIX)
    try:
        return _get_fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise ValidationError("Email account secret could not be decrypted with the configured email secret key.") from exc