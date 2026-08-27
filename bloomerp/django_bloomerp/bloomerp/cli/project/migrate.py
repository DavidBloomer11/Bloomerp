from __future__ import annotations

import click

from ._django import run_django_command


@click.command(
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": True,
    }
)
@click.argument("migrate_args", nargs=-1, type=click.UNPROCESSED)
def migrate(migrate_args: tuple[str, ...]) -> None:
    """Apply migrations and synchronize Bloomerp application fields.

    MIGRATE_ARGS are passed directly to Django's migrate command.
    """
    run_django_command("migrate", migrate_args)
    run_django_command("save_application_fields")
