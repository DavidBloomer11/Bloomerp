import click
import requests

from ..base import BLOOMERP_IO_URL

ENDPOINT = "/api/marketplace_apps/"

@click.command()
@click.argument("query", required=False)
def search(query: str | None) -> None:
    """Search marketplace apps, or list all apps when QUERY is omitted."""

    results = requests.get(
        BLOOMERP_IO_URL + ENDPOINT,
        params={"name__icontains": query} if query else None,
    ).json()

    if isinstance(results, dict):
        results = results.get("results", [])

    if not results:
        click.echo("No marketplace apps found.")
        return

    for app in results:
        click.secho(app["name"], bold=True)
        click.echo(f"  Slug: {app['slug']}")
        if description := app.get("description"):
            click.echo(f"  {description}")
        click.echo()
