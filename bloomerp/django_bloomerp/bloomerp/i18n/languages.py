from __future__ import annotations

from collections.abc import Iterable

from django.utils.translation import to_language, to_locale


def normalize_language_code(language: str) -> str:
    """Return the canonical Django runtime form, for example ``pt-br``."""

    value = str(language or "").strip().replace("_", "-")
    return to_language(value).lower() if value else ""


def catalog_locale(language: str) -> str:
    """Return the gettext/Babel locale form, for example ``pt_BR``."""

    normalized = normalize_language_code(language)
    return to_locale(normalized) if normalized else ""


def unique_languages(languages: Iterable[str]) -> list[str]:
    """Normalize and de-duplicate language codes while preserving order."""

    normalized = [normalize_language_code(language) for language in languages]
    return list(dict.fromkeys(language for language in normalized if language))
