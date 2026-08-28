from dataclasses import dataclass

import click

from bloomerp.cli.client import BloomerpCliClient


@dataclass
class Organization:
    name: str
    id: str


def get_organizations(client: BloomerpCliClient) -> list[Organization]:
    payload = client.request("GET", "/api/organizations/").json()
    if isinstance(payload, dict):
        payload = payload.get("results")
    if not isinstance(payload, list):
        raise click.ClickException(
            "Bloomerp.io returned an invalid organizations response."
        )

    return [
        Organization(name=str(entry["name"]), id=str(entry["id"]))
        for entry in payload
        if isinstance(entry, dict) and entry.get("name") and entry.get("id")
    ]

@click.command(name="list")
def list_organizations() -> None:
    """List organizations available to the current user."""
    client = BloomerpCliClient()
    organizations = get_organizations(client)

    click.echo("Available organizations:")
    for idx, org in enumerate(organizations, start=1):
        click.echo(f"   {idx}: {org.name}")
