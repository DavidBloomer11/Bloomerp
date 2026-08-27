from __future__ import annotations

import click

from ._django import run_django_command


@click.command(
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": True,
    }
)
@click.argument("makemigrations_args", nargs=-1, type=click.UNPROCESSED)
def makemigrations(makemigrations_args: tuple[str, ...]) -> None:
    """Create Django migrations for the current project.

    MAKEMIGRATIONS_ARGS are passed directly to Django's makemigrations command.
    """
    run_django_command("makemigrations", makemigrations_args)
