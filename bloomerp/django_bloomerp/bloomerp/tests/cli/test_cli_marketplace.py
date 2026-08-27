from bloomerp.cli.main import main


from click.testing import CliRunner


from unittest.mock import Mock, patch


@patch("bloomerp.cli.marketplace.search.requests.get")
def test_marketplace_search_prints_results(get: Mock):
    get.return_value.json.return_value = [
        {
            "name": "Inventory",
            "slug": "inventory",
            "description": "Stock management",
        }
    ]

    result = CliRunner().invoke(main, ["marketplace", "search"])

    assert result.exit_code == 0
    assert "Inventory" in result.output
    assert "Slug: inventory" in result.output
    assert "Stock management" in result.output


@patch("bloomerp.cli.marketplace.search.requests.get")
def test_marketplace_search_accepts_an_optional_query(get: Mock):
    get.return_value.json.return_value = []
    runner = CliRunner()

    without_query = runner.invoke(main, ["marketplace", "search"])
    with_query = runner.invoke(main, ["marketplace", "search", "inventory"])

    assert without_query.exit_code == 0
    assert with_query.exit_code == 0
    assert get.call_args_list[0].kwargs["params"] is None
    assert get.call_args_list[1].kwargs["params"] == {"name__icontains": "inventory"}