from __future__ import annotations

from pathlib import Path

import click

from .app._utils import find_app_dirs, read_app_state, resolve_app_dir
from .app.sync import (
    echo_app_sync,
    synchronize_app_from_remote,
    synchronize_app_to_remote,
    synchronize_local_app,
)
from .project.sync import (
    echo_project_sync,
    synchronize_local_project,
    synchronize_project_from_remote,
    synchronize_project_to_remote,
)
from .utils import get_project_state


def _selected_app_dirs(name: str | None) -> list[Path]:
    return [resolve_app_dir(name)] if name else find_app_dirs()


def _project_is_linked() -> bool:
    try:
        return bool(get_project_state().project_id)
    except click.ClickException:
        return False


def _has_remote_link(app_dirs: list[Path]) -> bool:
    return _project_is_linked() or any(
        read_app_state(app_dir).marketplace_app_id for app_dir in app_dirs
    )


@click.command("sync")
@click.argument("app_name", required=False)
@click.option("--from-remote", is_flag=True, help="Pull metadata for linked resources.")
@click.option("--to-remote", is_flag=True, help="Push metadata for linked resources.")
@click.option(
    "--force",
    is_flag=True,
    help="Back up and replace locally modified generated scaffold files.",
)
def sync(
    app_name: str | None,
    from_remote: bool,
    to_remote: bool,
    force: bool,
) -> None:
    """Synchronize the project and its Bloomerp apps."""

    if from_remote and to_remote:
        raise click.ClickException(
            "--from-remote and --to-remote cannot be used together."
        )

    app_dirs = _selected_app_dirs(app_name)
    if (from_remote or to_remote) and not _has_remote_link(app_dirs):
        raise click.ClickException(
            "The project or at least one selected app must be linked for remote sync."
        )

    project_linked = (
        _project_is_linked() if from_remote or to_remote else False
    )
    if from_remote:
        if project_linked:
            echo_project_sync(synchronize_project_from_remote(force=force))
        else:
            click.echo("Skipped remote project sync because the project is not linked.")
        for app_dir in app_dirs:
            if read_app_state(app_dir).marketplace_app_id:
                echo_app_sync(app_dir, synchronize_app_from_remote(app_dir))
            else:
                click.echo(
                    f"Skipped remote app sync for {app_dir.name} because it is not linked."
                )
        return

    for app_dir in app_dirs:
        if to_remote and read_app_state(app_dir).marketplace_app_id:
            manifest = synchronize_app_to_remote(app_dir)
        else:
            manifest = synchronize_local_app(app_dir)
            if to_remote:
                click.echo(
                    f"Skipped remote app sync for {app_dir.name} because it is not linked."
                )
        echo_app_sync(app_dir, manifest)

    if to_remote and project_linked:
        result = synchronize_project_to_remote(force=force)
    else:
        result = synchronize_local_project(force=force)
        if to_remote:
            click.echo("Skipped remote project sync because the project is not linked.")
    echo_project_sync(result)
