from __future__ import annotations

import click

from ..environment import add_environment_name, resolve_environment_name
from ..toml import write_toml_model
from ._utils import APP_MANIFEST_FILENAME, read_app_manifest, resolve_app_dir


@click.command("add-env")
@click.argument("variable_name", required=False)
@click.option("--name", "name_option", help="Environment variable name.")
@click.option("--app", "app_name", help="App whose manifest should be updated.")
@click.option("--required", is_flag=True, help="Mark the variable as required.")
def add_env(
    variable_name: str | None,
    name_option: str | None,
    app_name: str | None,
    required: bool,
) -> None:
    """Add an environment-variable declaration to an app manifest."""

    name = resolve_environment_name(variable_name, name_option)
    app_dir = resolve_app_dir(app_name)
    manifest = read_app_manifest(app_dir)
    manifest = manifest.model_copy(
        update={
            "environment": add_environment_name(
                manifest.environment,
                name,
                required=required,
            )
        }
    )
    write_toml_model(app_dir / APP_MANIFEST_FILENAME, manifest)
    classification = "required" if name in manifest.environment.required else "optional"
    click.echo(f"Added {name} as a {classification} environment variable for {manifest.name}.")
