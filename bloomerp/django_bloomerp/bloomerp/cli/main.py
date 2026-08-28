from __future__ import annotations

import click

from .app import app
from .auth import auth
from .marketplace import marketplace
from .organization import organization
from .project import project


@click.group()
def main() -> None:
    """Develop, extend, and deploy Bloomerp projects."""


main.add_command(auth)
main.add_command(organization)
main.add_command(project)
main.add_command(app)
main.add_command(marketplace)


if __name__ == "__main__":
    main()
