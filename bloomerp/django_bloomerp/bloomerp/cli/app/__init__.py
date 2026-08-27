from __future__ import annotations

import click

from .init import init


@click.group()
def app() -> None:
    """Create and publish reusable Bloomerp apps."""


app.add_command(init)


__all__ = ["app"]
