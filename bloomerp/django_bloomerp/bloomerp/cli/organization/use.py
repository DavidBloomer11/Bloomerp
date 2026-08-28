import click

from bloomerp.cli.client import BloomerpCliClient
from bloomerp.cli.credentials import save_organization_id
from bloomerp.cli.organization.list import Organization, get_organizations


ORGANIZATIONS_ENDPOINT = "/api/organizations/"


def _create_organization(client: BloomerpCliClient) -> Organization:
    name = click.prompt("Organization name").strip()
    if not name:
        raise click.ClickException("Organization name cannot be empty.")

    session = client.session()
    user = session.get("user") if isinstance(session, dict) else None
    user_id = user.get("id") if isinstance(user, dict) else None
    if not user_id:
        raise click.ClickException(
            "Bloomerp.io did not return the authenticated user needed to create "
            "the organization. Run 'bloomerp auth login' again."
        )

    payload = client.request(
        "POST",
        ORGANIZATIONS_ENDPOINT,
        json={"name": name, "owner": user_id},
    ).json()
    if not isinstance(payload, dict) or not payload.get("id"):
        raise click.ClickException(
            "Bloomerp.io returned an invalid organization creation response."
        )

    organization = Organization(
        name=str(payload.get("name") or name),
        id=str(payload["id"]),
    )
    click.echo(f"Created {organization.name} ({organization.id}).")
    return organization


@click.command()
def use() -> None:
    """Select an organization for future commands."""
    client = BloomerpCliClient()
    organizations = get_organizations(client)

    click.echo("Please select the organization you want to use, or create a new one.\n")
    click.echo("Available organizations:")
    for idx, org in enumerate(organizations, start=1):
        click.echo(f"   {idx}: {org.name} ({org.id})")

    create_index = len(organizations) + 1
    click.echo(f"   {create_index}: Create a new organization.")
    selection = click.prompt(
        "Select an organization",
        type=click.IntRange(1, create_index),
    )

    organization = (
        _create_organization(client)
        if selection == create_index
        else organizations[selection - 1]
    )
    client.organization_id = organization.id
    save_organization_id(organization.id, client.server_url)
    click.echo(f"Using organization {organization.name} ({organization.id}).")
