from bloomerp.cli.main import main


from click.testing import CliRunner


import tomllib
from pathlib import Path


def test_app_init_creates_an_independent_app_manifest():
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(main, ["app", "init", "sales-tools"])

        assert result.exit_code == 0
        assert Path("apps/sales_tools/apps.py").is_file()
        manifest = tomllib.loads(
            Path("apps/sales_tools/bloomerp.toml").read_text(encoding="utf-8")
        )
        assert manifest["name"] == "sales_tools"