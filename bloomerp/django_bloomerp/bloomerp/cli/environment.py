from __future__ import annotations

import re

import click

from .base import BloomerpEnvironment


ENVIRONMENT_VARIABLE_NAME_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{0,254}$")


def resolve_environment_name(
    argument_name: str | None,
    option_name: str | None,
) -> str:
    """Resolve and validate an environment-variable name from CLI input."""

    if argument_name and option_name and argument_name != option_name:
        raise click.ClickException(
            "Pass the environment variable name either as an argument or with "
            "--name, not both."
        )

    name = argument_name or option_name
    if name is None:
        name = click.prompt("Environment variable name")
    normalized = name.strip().upper()
    if not ENVIRONMENT_VARIABLE_NAME_PATTERN.fullmatch(normalized):
        raise click.ClickException(
            "Environment variable names must start with a letter and contain "
            "only uppercase letters, numbers, and underscores."
        )
    return normalized


def add_environment_name(
    environment: BloomerpEnvironment,
    name: str,
    *,
    required: bool,
) -> BloomerpEnvironment:
    """Return an environment declaration containing NAME exactly once."""

    required_names = set(environment.required)
    optional_names = set(environment.optional)
    if required:
        required_names.add(name)
        optional_names.discard(name)
    elif name not in required_names:
        optional_names.add(name)

    return environment.model_copy(
        update={
            "required": sorted(required_names),
            "optional": sorted(optional_names - required_names),
        }
    )


def merge_environments(*environments: BloomerpEnvironment) -> BloomerpEnvironment:
    """Return the deterministic union of environment declarations."""

    required = {
        name
        for environment in environments
        for name in environment.required
    }
    optional = {
        name
        for environment in environments
        for name in environment.optional
    }
    return BloomerpEnvironment(
        required=sorted(required),
        optional=sorted(optional - required),
    )
