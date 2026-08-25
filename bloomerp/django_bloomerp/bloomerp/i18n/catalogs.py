from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from babel.messages.catalog import Catalog, Message
from babel.messages.pofile import read_po, write_po

PLACEHOLDER_RE = re.compile(
    r"%\([^)]+\)[#0 +\-]?(?:\d+|\*)?(?:\.\d+|\.\*)?[diouxXeEfFgGcrs%]"
    r"|(?<!\{)\{[A-Za-z_][A-Za-z0-9_.]*(?:![rsa])?(?::[^{}]+)?\}(?!\})"
)
TAG_RE = re.compile(r"</?[A-Za-z][^>]*>")


def _location_sort_key(location: tuple[str, int | None]) -> tuple[str, int]:
    filename, line_number = location
    return filename, line_number if line_number is not None else -1


def catalog_path(app_path: Path, language: str, domain: str) -> Path:
    return app_path / "locale" / language / "LC_MESSAGES" / f"{domain}.po"


def read_catalog(path: Path, language: str, domain: str) -> Catalog:
    if path.exists():
        with path.open("r", encoding="utf-8") as source:
            return read_po(source, locale=language, domain=domain)
    return Catalog(locale=language, domain=domain)


def save_catalog(catalog: Catalog, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as destination:
        write_po(destination, catalog, width=100, sort_output=True)


def merge_messages(
    path: Path,
    language: str,
    domain: str,
    messages: Iterable[dict],
    *,
    prune: bool = False,
    prune_contexts: set[str] | None = None,
) -> int:
    catalog = read_catalog(path, language, domain)
    messages = list(messages)
    if prune:
        template = Catalog(domain=domain)
        for item in messages:
            template.add(
                item["message"],
                context=item.get("context"),
                locations=[tuple(location) for location in item.get("locations", [])],
            )
        existing_ids = {(message.id, message.context) for message in catalog if message.id}
        catalog.update(template, no_fuzzy_matching=True)
        added = sum(
            (message.id, message.context) not in existing_ids
            for message in template
            if message.id
        )
        save_catalog(catalog, path)
        return added

    added = 0
    if prune_contexts:
        desired = {
            (item["message"], item.get("context"))
            for item in messages
        }
        for message in list(catalog):
            if (
                message.id
                and message.context in prune_contexts
                and (message.id, message.context) not in desired
            ):
                catalog.delete(message.id, context=message.context)
        for key, message in list(catalog.obsolete.items()):
            if (
                message.context in prune_contexts
                and (message.id, message.context) not in desired
            ):
                del catalog.obsolete[key]

    for item in messages:
        message_id = item["message"]
        context = item.get("context")
        existing = catalog.get(message_id, context=context)
        obsolete_key = next(
            (
                key
                for key, obsolete_message in catalog.obsolete.items()
                if obsolete_message.id == message_id
                and obsolete_message.context == context
            ),
            None,
        )
        obsolete = (
            catalog.obsolete.pop(obsolete_key)
            if obsolete_key is not None
            else None
        )
        locations = [tuple(location) for location in item.get("locations", [])]
        if existing:
            if obsolete and not all(translated_values(existing)) and all(
                translated_values(obsolete)
            ):
                existing.string = obsolete.string
                existing.flags.update(obsolete.flags)
            existing.locations = sorted(
                set(existing.locations).union(locations),
                key=_location_sort_key,
            )
            continue
        catalog.add(
            message_id,
            string=obsolete.string if obsolete else None,
            context=context,
            locations=locations,
            flags=obsolete.flags if obsolete else (),
        )
        added += 1
    save_catalog(catalog, path)
    return added


def translated_values(message: Message) -> list[str]:
    if isinstance(message.string, tuple):
        return list(message.string)
    return [message.string or ""]


def approve_translated_messages(catalog: Catalog) -> int:
    approved = 0
    for message in catalog:
        if (
            message.id
            and "fuzzy" in message.flags
            and all(translated_values(message))
        ):
            message.flags.discard("fuzzy")
            approved += 1
    return approved


def reconcile_obsolete_messages(catalog: Catalog) -> int:
    """Remove obsolete copies that conflict with active model-derived messages."""

    reconciled = 0
    for key, obsolete in list(catalog.obsolete.items()):
        active = catalog.get(obsolete.id, context=obsolete.context)
        if active is None:
            continue
        if not all(translated_values(active)) and all(translated_values(obsolete)):
            active.string = obsolete.string
            active.flags.update(obsolete.flags)
        del catalog.obsolete[key]
        reconciled += 1
    return reconciled


def source_values(message: Message) -> list[str]:
    if isinstance(message.id, tuple):
        return list(message.id)
    return [message.id]


def validate_message(message: Message) -> list[str]:
    if not message.id:
        return []
    errors: list[str] = []
    sources = source_values(message)
    translations = translated_values(message)
    for index, translation in enumerate(translations):
        if not translation:
            continue
        source = sources[min(index, len(sources) - 1)]
        if sorted(PLACEHOLDER_RE.findall(source)) != sorted(PLACEHOLDER_RE.findall(translation)):
            errors.append(f"placeholder mismatch in plural form {index}")
        if sorted(TAG_RE.findall(source)) != sorted(TAG_RE.findall(translation)):
            errors.append(f"HTML tag mismatch in plural form {index}")
    return errors
