from __future__ import annotations

import click



from .build import build
from .check import check
from .deploy import deploy
from .init import init
from .link import link
from .makemigrations import makemigrations
from .migrate import migrate
from .run import run
from .scaffold_sync import scaffold_sync
from .sync import sync
from .upload import upload

@click.group()
def project() -> None:
    """Create, validate, and deploy Bloomerp projects."""


project.add_command(init)
project.add_command(check)
project.add_command(build)
project.add_command(link)
project.add_command(deploy)
project.add_command(makemigrations)
project.add_command(migrate)
project.add_command(run)
project.add_command(scaffold_sync)
project.add_command(sync)
project.add_command(upload)

__all__ = ["project"]
