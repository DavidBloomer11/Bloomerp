from __future__ import annotations

import click

from ..environment import add_environment_name, resolve_environment_name
from ..utils import get_project_manifest, write_project_manifest


@click.command("add-env")
@click.argument("variable_name", required=False)
@click.option("--name", "name_option", help="Environment variable name.")
@click.option("--required", is_flag=True, help="Mark the variable as required.")
def add_env(
    variable_name: str | None,
    name_option: str | None,
    required: bool,
) -> None:
    """Add an environment-variable declaration to the project manifest."""

    name = resolve_environment_name(variable_name, name_option)
    manifest = get_project_manifest()
    manifest = manifest.model_copy(
        update={
            "environment": add_environment_name(
                manifest.environment,
                name,
                required=required,
            )
        }
    )
    write_project_manifest(manifest)
    classification = "required" if name in manifest.environment.required else "optional"
    click.echo(f"Added {name} as a {classification} project environment variable.")
