from __future__ import annotations

import click

from .login import login
from .logout import logout
from .status import status


@click.group()
def auth() -> None:
    """Manage Bloomerp.io authentication."""


auth.add_command(login)
auth.add_command(status)
auth.add_command(logout)

__all__ = ["auth"]
