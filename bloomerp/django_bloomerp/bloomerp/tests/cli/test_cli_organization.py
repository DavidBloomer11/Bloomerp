from unittest.mock import Mock, call, patch

from click.testing import CliRunner

from bloomerp.cli.main import main
from bloomerp.cli.organization.list import Organization


@patch("bloomerp.cli.organization.use.save_organization_id")
@patch("bloomerp.cli.organization.use.get_organizations")
@patch("bloomerp.cli.organization.use.BloomerpCliClient")
def test_organization_use_stores_the_selected_organization_on_the_client(
    client_type: Mock,
    get_organizations: Mock,
    save_organization_id: Mock,
):
    client = client_type.return_value
    client.server_url = "https://api.example"
    get_organizations.return_value = [
        Organization(name="First", id="organization-1"),
        Organization(name="Second", id="organization-2"),
    ]

    result = CliRunner().invoke(main, ["organization", "use"], input="2\n")

    assert result.exit_code == 0
    assert "3: Create a new organization" in result.output
    assert "Using organization Second" in result.output
    assert client.organization_id == "organization-2"
    save_organization_id.assert_called_once_with(
        "organization-2", "https://api.example"
    )


@patch("bloomerp.cli.organization.use.save_organization_id")
@patch("bloomerp.cli.organization.use.get_organizations")
@patch("bloomerp.cli.organization.use.BloomerpCliClient")
def test_organization_use_creates_selects_and_stores_a_new_organization(
    client_type: Mock,
    get_organizations: Mock,
    save_organization_id: Mock,
):
    client = client_type.return_value
    client.server_url = "https://api.example"
    client.session.return_value = {"user": {"id": 42}}
    response = Mock()
    response.json.return_value = {"id": "organization-new", "name": "New Org"}
    client.request.return_value = response
    get_organizations.return_value = [
        Organization(name="Existing", id="organization-existing")
    ]

    result = CliRunner().invoke(
        main,
        ["organization", "use"],
        input="2\nNew Org\n",
    )

    assert result.exit_code == 0
    assert "Created New Org (organization-new)" in result.output
    assert "Using organization New Org" in result.output
    assert client.organization_id == "organization-new"
    assert client.request.call_args_list == [
        call(
            "POST",
            "/api/organizations/",
            json={"name": "New Org", "owner": 42},
        )
    ]
    save_organization_id.assert_called_once_with(
        "organization-new", "https://api.example"
    )
