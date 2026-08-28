import json
import tomllib
import zipfile
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from bloomerp.cli.app.build import build_app_wheel
from bloomerp.cli.base import (
    BloomerpAppDjango,
    BloomerpAppManifest,
    BloomerpAppModel,
    BloomerpAppModule,
    BloomerpEnvironment,
)
from bloomerp.cli.main import main
from bloomerp.cli.toml import write_toml_model


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload


def initialize_local_project(runner: CliRunner):
    result = runner.invoke(
        main,
        ["project", "init", ".", "--name", "CLI App Tests", "--no-app", "--no-input"],
    )
    assert result.exit_code == 0, result.output


def test_app_init_creates_an_independent_app_manifest():
    runner = CliRunner()

    with runner.isolated_filesystem():
        initialize_local_project(runner)
        result = runner.invoke(main, ["app", "init", "sales-tools"])

        assert result.exit_code == 0
        assert Path("apps/sales_tools/apps.py").is_file()
        manifest = tomllib.loads(
            Path("apps/sales_tools/app.bloomerp.toml").read_text(encoding="utf-8")
        )
        assert manifest["name"] == "sales_tools"
        assert manifest["environment"] == {"required": [], "optional": []}


def test_app_environment_defaults_are_independent():
    first = BloomerpAppManifest(name="first")
    second = BloomerpAppManifest(name="second")

    first.environment.required.append("FIRST_API_KEY")

    assert first.environment.required == ["FIRST_API_KEY"]
    assert second.environment.required == []


def test_app_manifest_preserves_declared_environment_requirements():
    runner = CliRunner()

    with runner.isolated_filesystem():
        app_dir = Path("apps/sample_app")
        app_dir.mkdir(parents=True)
        write_toml_model(
            app_dir / "app.bloomerp.toml",
            BloomerpAppManifest(
                name="sample_app",
                environment=BloomerpEnvironment(
                    required=["SAMPLE_API_KEY"],
                    optional=["SAMPLE_API_URL"],
                ),
            ),
        )

        manifest = tomllib.loads(
            (app_dir / "app.bloomerp.toml").read_text(encoding="utf-8")
        )

        assert manifest["environment"] == {
            "required": ["SAMPLE_API_KEY"],
            "optional": ["SAMPLE_API_URL"],
        }


def create_local_app(app_name="sample_app"):
    Path(".bloomerp").mkdir()
    app_dir = Path("apps") / app_name
    app_dir.mkdir(parents=True)
    write_toml_model(
        app_dir / "app.bloomerp.toml",
        BloomerpAppManifest(
            name=app_name,
            version="1.2.0",
            description="Reusable workflows.",
            django=BloomerpAppDjango(
                app_config=f"apps.{app_name}.apps.SampleAppConfig"
            ),
            modules=[
                BloomerpAppModule(
                    id="sample",
                    name="Sample",
                    description="Sample workflows.",
                )
            ],
            models=[
                BloomerpAppModel(
                    name="SampleRecord",
                    database_table="sample_record",
                )
            ],
        ),
    )
    return app_dir


def test_app_manifest_writes_structured_modules():
    runner = CliRunner()

    with runner.isolated_filesystem():
        app_dir = create_local_app()

        manifest = tomllib.loads(
            (app_dir / "app.bloomerp.toml").read_text(encoding="utf-8")
        )

        assert manifest["django"]["app_config"] == (
            "apps.sample_app.apps.SampleAppConfig"
        )
        assert manifest["modules"] == [
            {
                "id": "sample",
                "name": "Sample",
                "description": "Sample workflows.",
            }
        ]
        assert manifest["models"] == [
            {"name": "SampleRecord", "database_table": "sample_record"}
        ]
        assert "manifest_version" not in manifest


def test_app_build_creates_a_wheel_with_the_app_manifest():
    runner = CliRunner()

    with runner.isolated_filesystem():
        initialize_local_project(runner)
        result = runner.invoke(main, ["app", "init", "sample-app"])
        assert result.exit_code == 0, result.output

        wheel = build_app_wheel(Path("apps/sample_app"), Path("dist"))

        assert wheel.name.startswith("sample_app-0.1.0-")
        with zipfile.ZipFile(wheel) as archive:
            assert "apps/sample_app/app.bloomerp.toml" in archive.namelist()


def test_app_link_selects_an_existing_marketplace_app():
    runner = CliRunner()
    remote_app = {
        "id": "72c02ab4-d5a7-4ee8-acd6-cce670a3babb",
        "name": "Sample App",
        "slug": "sample-app",
        "owner": "5f0d014c-3e77-44e1-8010-a9b317905669",
    }

    class FakeClient:
        def request(self, method, path, **kwargs):
            assert method == "GET"
            assert path == "/api/marketplace_apps/"
            return FakeResponse([remote_app])

    with runner.isolated_filesystem():
        create_local_app()
        with patch("bloomerp.cli.app.link.BloomerpCliClient", return_value=FakeClient()):
            result = runner.invoke(main, ["app", "link", "sample-app"], input="1\n")

        assert result.exit_code == 0, result.output
        state = tomllib.loads(
            Path(".bloomerp/apps/sample_app.toml").read_text(encoding="utf-8")
        )
        assert state["marketplace_app_id"] == remote_app["id"]


def test_app_link_can_create_a_private_marketplace_app():
    runner = CliRunner()
    requests = []

    class FakeClient:
        def request(self, method, path, **kwargs):
            requests.append((method, path, kwargs))
            if method == "GET":
                return FakeResponse([])
            return FakeResponse(
                {
                    "id": "72c02ab4-d5a7-4ee8-acd6-cce670a3babb",
                    "name": "Sample App",
                    "slug": "sample-app",
                    "owner": "5f0d014c-3e77-44e1-8010-a9b317905669",
                    "is_public": False,
                },
                status_code=201,
            )

        def session(self):
            return {"user": {"id": "5f0d014c-3e77-44e1-8010-a9b317905669"}}

    with runner.isolated_filesystem():
        create_local_app()
        with patch("bloomerp.cli.app.link.BloomerpCliClient", return_value=FakeClient()):
            result = runner.invoke(main, ["app", "link", "sample-app"], input="1\n")

    assert result.exit_code == 0, result.output
    _method, _path, kwargs = requests[-1]
    assert kwargs["json"] == {
        "name": "Sample App",
        "slug": "sample-app",
        "description": "Reusable workflows.",
        "owner": "5f0d014c-3e77-44e1-8010-a9b317905669",
    }


def test_app_upload_uses_linked_marketplace_app_and_manifest():
    runner = CliRunner()
    requests = []

    class FakeClient:
        def request(self, method, path, **kwargs):
            requests.append((method, path, kwargs))
            return FakeResponse(
                {
                    "version_id": "68d60a8e-072f-4f3e-b754-172576c98295",
                    "version": "1.2.0",
                    "created": True,
                },
                status_code=201,
            )

    with runner.isolated_filesystem():
        create_local_app()
        Path(".bloomerp/apps").mkdir()
        Path(".bloomerp/apps/sample_app.toml").write_text(
            'marketplace_app_id = "72c02ab4-d5a7-4ee8-acd6-cce670a3babb"\n',
            encoding="utf-8",
        )
        wheel = Path("sample_app-1.2.0-py3-none-any.whl")
        wheel.write_bytes(b"wheel")
        with patch("bloomerp.cli.app.upload.BloomerpCliClient", return_value=FakeClient()):
            result = runner.invoke(
                main,
                ["app", "upload", "sample-app", "--wheel", str(wheel)],
            )

    assert result.exit_code == 0, result.output
    method, path, kwargs = requests[0]
    assert method == "POST"
    assert path == "/api/marketplace_apps/upload/"
    assert kwargs["data"]["marketplace_app_id"] == (
        "72c02ab4-d5a7-4ee8-acd6-cce670a3babb"
    )
    uploaded_manifest = json.loads(kwargs["data"]["manifest"])
    assert uploaded_manifest["modules"] == [
        {
            "id": "sample",
            "name": "Sample",
            "description": "Sample workflows.",
        }
    ]
    assert "manifest_version" not in uploaded_manifest


def test_app_upload_requires_link_first():
    runner = CliRunner()

    with runner.isolated_filesystem():
        create_local_app()
        result = runner.invoke(main, ["app", "upload", "sample-app"])

    assert result.exit_code != 0
    assert "bloomerp app link" in result.output
