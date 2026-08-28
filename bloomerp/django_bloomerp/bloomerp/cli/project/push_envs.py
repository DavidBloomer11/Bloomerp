from __future__ import annotations

import ast
import re
from pathlib import Path

import click

from bloomerp.cli.client import BloomerpCliClient
from bloomerp.cli.utils import (
    get_project_manifest,
    get_project_metadata_dir,
    get_project_state,
)


ENVIRONMENT_VARIABLE_NAME_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{0,254}$")


def _parse_quoted_value(value: str, *, line_number: int) -> str:
    quote = value[0]
    escaped = False
    closing_index = None
    for index, character in enumerate(value[1:], start=1):
        if character == "\\" and not escaped:
            escaped = True
            continue
        if character == quote and not escaped:
            closing_index = index
            break
        escaped = False

    if closing_index is None:
        raise click.ClickException(
            f"Invalid .env file: unterminated quoted value on line {line_number}."
        )

    remainder = value[closing_index + 1 :].strip()
    if remainder and not remainder.startswith("#"):
        raise click.ClickException(
            f"Invalid .env file: unexpected content on line {line_number}."
        )

    literal = value[: closing_index + 1]
    try:
        parsed = ast.literal_eval(literal)
    except (SyntaxError, ValueError) as exc:
        raise click.ClickException(
            f"Invalid .env file: invalid quoted value on line {line_number}."
        ) from exc
    return str(parsed)


def _parse_unquoted_value(value: str) -> str:
    for index, character in enumerate(value):
        if character == "#" and (index == 0 or value[index - 1].isspace()):
            return value[:index].rstrip()
    return value.strip()


def parse_env_file(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except FileNotFoundError as exc:
        raise click.ClickException(f"Environment file not found: {path}") from exc
    except OSError as exc:
        raise click.ClickException(
            f"Could not read environment file {path}: {exc}"
        ) from exc

    variables: dict[str, str] = {}
    for line_number, source_line in enumerate(lines, start=1):
        line = source_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            raise click.ClickException(
                f"Invalid .env file: expected NAME=VALUE on line {line_number}."
            )

        raw_name, raw_value = line.split("=", 1)
        name = raw_name.strip().upper()
        if not ENVIRONMENT_VARIABLE_NAME_PATTERN.fullmatch(name):
            raise click.ClickException(
                f"Invalid environment variable name on line {line_number}: "
                f"{raw_name.strip() or '(empty)'}"
            )

        stripped_value = raw_value.strip()
        value = (
            _parse_quoted_value(stripped_value, line_number=line_number)
            if stripped_value.startswith(("'", '"'))
            else _parse_unquoted_value(raw_value)
        )
        if not value:
            raise click.ClickException(
                f"Environment variable {name} on line {line_number} has an empty value."
            )
        if "\x00" in value or "\n" in value or "\r" in value:
            raise click.ClickException(
                f"Environment variable {name} must contain exactly one line."
            )
        variables[name] = value

    if not variables:
        raise click.ClickException(f"No environment variables found in {path}.")
    return variables


def _select_source() -> str:
    click.echo("How would you like to provide the environment variables?")
    click.echo("  1. Use a .env file")
    click.echo("  2. Enter them manually")
    selection = click.prompt("Select a source", type=click.IntRange(1, 2))
    return "env-file" if selection == 1 else "manual"


def _prompt_required_value(name: str) -> str:
    while True:
        value = click.prompt(name, hide_input=True, default="", show_default=False)
        if value:
            return value
        click.echo(f"{name} is required and cannot be skipped.", err=True)


def _prompt_manifest_variables() -> dict[str, str]:
    environment = get_project_manifest().environment
    required_names = list(dict.fromkeys(environment.required))
    optional_names = [
        name
        for name in dict.fromkeys(environment.optional)
        if name not in required_names
    ]
    if not required_names and not optional_names:
        raise click.ClickException(
            "The project manifest does not declare any environment variables."
        )

    variables = {
        name: _prompt_required_value(name)
        for name in required_names
    }
    for name in optional_names:
        value = click.prompt(
            f"{name} (optional; leave blank to skip)",
            hide_input=True,
            default="",
            show_default=False,
        )
        if value:
            variables[name] = value
    return variables


def _load_file_variables() -> dict[str, str]:
    project_root = get_project_metadata_dir().parent
    entered_path = click.prompt("Path to .env file", default=".env")
    path = Path(entered_path).expanduser()
    if not path.is_absolute():
        path = project_root / path
    return parse_env_file(path.resolve())


@click.command()
def push_envs() -> None:
    """Push project environment variables to Bloomerp.io as secrets."""
    state = get_project_state()
    if not state.project_id:
        raise click.ClickException(
            "This project is not linked. Run 'bloomerp project link' first."
        )

    source = _select_source()
    variables = (
        _load_file_variables()
        if source == "env-file"
        else _prompt_manifest_variables()
    )
    if not variables:
        click.echo("No environment variables selected; nothing was pushed.")
        return

    response = BloomerpCliClient().request(
        "POST",
        f"/api/projects/{state.project_id}/push-envs/",
        json={
            "variables": [
                {"name": name, "value": value}
                for name, value in variables.items()
            ]
        },
    )
    payload = response.json()
    total = payload.get("total") if isinstance(payload, dict) else None
    if not isinstance(total, int):
        raise click.ClickException(
            "Bloomerp.io returned an invalid environment variable response."
        )
    click.echo(
        f"Pushed {total} environment variable{'s' if total != 1 else ''} "
        "to Bloomerp.io."
    )
