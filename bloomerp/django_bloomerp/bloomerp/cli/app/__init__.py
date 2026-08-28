from __future__ import annotations

import click

from .init import init
from .link import link
from .sync_manifest import sync_manifest
from .upload import upload


@click.group()
def app() -> None:
    """Create and publish reusable Bloomerp apps."""


app.add_command(init)
app.add_command(link)
app.add_command(sync_manifest)
app.add_command(upload)


__all__ = ["app"]
