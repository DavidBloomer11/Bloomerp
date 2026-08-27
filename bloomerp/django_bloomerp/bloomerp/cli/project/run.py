from __future__ import annotations

import click

from ._django import run_django_command


@click.command(
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": True,
    }
)
@click.argument("runserver_args", nargs=-1, type=click.UNPROCESSED)
def run(runserver_args: tuple[str, ...]) -> None:
    """Run the current project using Django's development server.

    RUNSERVER_ARGS are passed directly to Django's runserver command.
    """
    try:
        run_django_command("runserver", runserver_args)
    except KeyboardInterrupt:
        return
    
