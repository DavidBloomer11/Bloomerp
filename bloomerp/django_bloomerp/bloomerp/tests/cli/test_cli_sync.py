import tomllib
from pathlib import Path
from unittest.mock import Mock, call, patch

from click.testing import CliRunner

from bloomerp.cli.base import (
    BloomerpAppManifest,
    BloomerpAppModule,
    BloomerpEnvironment,
    BloomerpProjectManifest,
    BloomerpProjectState,
    BloomerpRuntime,
)
from bloomerp.cli.main import main
from bloomerp.cli.toml import write_toml_model


def create_project(*, linked: bool = False) -> None:
    metadata_dir = Path(".bloomerp")
    metadata_dir.mkdir()
    write_toml_model(
        metadata_dir / "project.bloomerp.toml",
        BloomerpProjectManifest(
            name="Example",
            description="Local project",
            environment=BloomerpEnvironment(
                required=["PROJECT_TOKEN"],
                optional=["SHARED_KEY"],
            ),
            runtime=BloomerpRuntime(
                bloomerp_version="1.14.6",
                python_version="3.13",
            ),
        ),
    )
    write_toml_model(
        metadata_dir / "state.toml",
        BloomerpProjectState(project_id="project-1" if linked else ""),
        exclude_defaults=True,
    )


def create_app(*, linked: bool = False) -> Path:
    app_dir = Path("apps/sample_app")
    app_dir.mkdir(parents=True)
    write_toml_model(
        app_dir / "app.bloomerp.toml",
        BloomerpAppManifest(
            name="sample_app",
            version="2.3.0",
            required_version=">=1.14,<2",
            description="Local description",
            tagline="Local tagline",
            environment=BloomerpEnvironment(
                required=["APP_TOKEN", "SHARED_KEY"],
                optional=["APP_REGION"],
            ),
            modules=[
                BloomerpAppModule(
                    id="sample",
                    name="Sample",
                    description="Sample module",
                )
            ],
        ),
    )
    if linked:
        state_dir = Path(".bloomerp/apps")
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "sample_app.toml").write_text(
            'app_id = "app-1"\n',
            encoding="utf-8",
        )
    return app_dir


def test_project_sync_merges_app_environment_declarations():
    """
    Use case: A project contains overlapping project and app environment declarations.
    Expected result: Project sync writes a stable union where required wins.
    """
    runner = CliRunner()

    with runner.isolated_filesystem():
        # 1. Create a project and app with overlapping declarations.
        create_project()
        create_app()

        # 2. Synchronize while isolating scaffold file behavior.
        with patch(
            "bloomerp.cli.project.sync.synchronize_scaffold",
            return_value=([], [], None),
        ):
            result = runner.invoke(main, ["project", "sync"])

        # 3. Verify the deterministic merged declaration.
        assert result.exit_code == 0, result.output
        manifest = tomllib.loads(
            Path(".bloomerp/project.bloomerp.toml").read_text(encoding="utf-8")
        )
        assert manifest["environment"] == {
            "required": ["APP_TOKEN", "PROJECT_TOKEN", "SHARED_KEY"],
            "optional": ["APP_REGION"],
        }


def test_project_sync_from_remote_reads_only_manifest():
    from bloomerp.cli.utils import get_project_manifest, get_project_state
    with CliRunner().isolated_filesystem():
        create_project(linked=True)
        manifest = get_project_manifest().model_dump(mode="json")
        manifest["name"] = "Remote Example"
        manifest["environment"] = {"required": ["REMOTE_REQUIRED"], "optional": ["REMOTE_OPTIONAL"]}
        client = Mock()
        client.request.return_value.json.return_value = {"manifest": manifest, "revision": "revision-2"}
        with patch("bloomerp.cli.project.sync.BloomerpCliClient", return_value=client), patch("bloomerp.cli.project.sync.synchronize_scaffold", return_value=([], [], None)):
            result = CliRunner().invoke(main, ["project", "sync", "--from-remote"])
        assert result.exit_code == 0, result.output
        assert get_project_manifest().environment.required == ["REMOTE_REQUIRED"]
        assert get_project_state().manifest_revision == "revision-2"
        client.request.assert_called_once_with("GET", "/api/projects/project-1/manifest/")


def test_project_sync_to_remote_registers_local_app_without_uploading():
    from bloomerp.cli.utils import get_project_state
    with CliRunner().isolated_filesystem():
        create_project(linked=True)
        Path(".bloomerp/state.toml").write_text('project_id = "project-1"\nmanifest_revision = "revision-1"\n')
        create_app()
        client = Mock()
        client.session.return_value = {"user": {"id": 42}}
        app_id = "11111111-1111-4111-8111-111111111111"
        def request(method, endpoint, **kwargs):
            if endpoint == "/api/apps/":
                return Mock(json=Mock(return_value={"id": app_id}))
            assert endpoint == "/api/projects/project-1/manifest/"
            assert kwargs["json"]["base_revision"] == "revision-1"
            assert kwargs["json"]["manifest"]["apps"] == [{"id": app_id, "name": "sample_app"}]
            return Mock(json=Mock(return_value={"manifest": kwargs["json"]["manifest"], "revision": "revision-2"}))
        client.request.side_effect = request
        with patch("bloomerp.cli.project.sync.BloomerpCliClient", return_value=client), patch("bloomerp.cli.project.sync.synchronize_scaffold", return_value=([], [], None)):
            result = CliRunner().invoke(main, ["project", "sync", "--to-remote"])
        assert result.exit_code == 0, result.output
        assert get_project_state().manifest_revision == "revision-2"
        assert get_project_state().snapshot_id == ""
        assert client.request.call_count == 2


def test_app_sync_from_remote_preserves_release_and_application_state():
    """
    Use case: A linked app pulls editable marketplace metadata.
    Expected result: Release compatibility and discovered app state remain local.
    """
    runner = CliRunner()
    client = Mock()
    response = Mock()
    response.json.return_value = {
        "name": "Remote app",
        "description": "Remote description",
        "tagline": "Remote tagline",
        "version": "99.0.0",
        "modules": [],
    }
    client.request.return_value = response

    with runner.isolated_filesystem():
        # 1. Create a linked app with local release and module state.
        create_project()
        app_dir = create_app(linked=True)

        # 2. Pull only remote marketplace metadata.
        with patch(
            "bloomerp.cli.app.sync.BloomerpCliClient",
            return_value=client,
        ):
            result = runner.invoke(main, ["app", "sync", "sample_app", "--from-remote"])

        # 3. Verify remote version and modules were ignored.
        assert result.exit_code == 0, result.output
        manifest = tomllib.loads(
            (app_dir / "app.bloomerp.toml").read_text(encoding="utf-8")
        )
        assert manifest["name"] == "sample_app"
        assert manifest["display_name"] == "Remote app"
        assert manifest["description"] == "Remote description"
        assert manifest["tagline"] == "Remote tagline"
        assert manifest["version"] == "2.3.0"
        assert manifest["required_version"] == ">=1.14,<2"
        assert manifest["modules"] == [
            {"id": "sample", "name": "Sample", "description": "Sample module"}
        ]


def test_app_sync_to_remote_excludes_release_version():
    """
    Use case: A linked app pushes its editable marketplace metadata.
    Expected result: The metadata request does not alter app release versions.
    """
    runner = CliRunner()
    client = Mock()
    client.request.return_value = Mock()

    with runner.isolated_filesystem():
        # 1. Create a linked app and load its manifest.
        create_project()
        app_dir = create_app(linked=True)
        manifest = BloomerpAppManifest.model_validate(
            tomllib.loads(
                (app_dir / "app.bloomerp.toml").read_text(encoding="utf-8")
            )
        )

        # 2. Push metadata while replacing Django discovery with its local result.
        with (
            patch(
                "bloomerp.cli.app.sync.BloomerpCliClient",
                return_value=client,
            ),
            patch(
                "bloomerp.cli.app.sync.synchronize_local_app",
                return_value=manifest,
            ),
        ):
            result = runner.invoke(main, ["app", "sync", "sample_app", "--to-remote"])

        # 3. Verify only editable marketplace fields were sent.
        assert result.exit_code == 0, result.output
        client.request.assert_called_once_with(
            "PATCH",
            "/api/apps/app-1/",
            json={
                "name": "Sample App",
                "description": "Local description",
                "tagline": "Local tagline",
            },
        )


def test_add_env_commands_support_explicit_app_selection_and_required_wins():
    """
    Use case: Environment declarations are added through project and app commands.
    Expected result: Names normalize and a required declaration overrides optional.
    """
    runner = CliRunner()

    with runner.isolated_filesystem():
        # 1. Create the local manifests.
        create_project()
        app_dir = create_app()

        # 2. Add project and app declarations using both supported name forms.
        project_result = runner.invoke(
            main,
            ["project", "add-env", "new_token", "--required"],
        )
        app_result = runner.invoke(
            main,
            ["app", "add-env", "--name=app_region", "--app", "sample_app", "--required"],
        )

        # 3. Verify normalization, targeting, and required precedence.
        assert project_result.exit_code == 0, project_result.output
        assert app_result.exit_code == 0, app_result.output
        project_manifest = tomllib.loads(
            Path(".bloomerp/project.bloomerp.toml").read_text(encoding="utf-8")
        )
        app_manifest = tomllib.loads(
            (app_dir / "app.bloomerp.toml").read_text(encoding="utf-8")
        )
        assert project_manifest["environment"]["required"] == [
            "NEW_TOKEN",
            "PROJECT_TOKEN",
        ]
        assert app_manifest["environment"]["required"] == [
            "APP_REGION",
            "APP_TOKEN",
            "SHARED_KEY",
        ]
        assert app_manifest["environment"]["optional"] == []


def test_combined_sync_runs_apps_then_project_without_requiring_link_state():
    """
    Use case: A local-only project runs the aggregate sync command.
    Expected result: Every selected app syncs before the project without a link.
    """
    runner = CliRunner()

    with runner.isolated_filesystem():
        # 1. Create local manifests and remove optional remote-link state.
        create_project()
        app_dir = create_app()
        Path(".bloomerp/state.toml").unlink()
        app_manifest = BloomerpAppManifest.model_validate(
            tomllib.loads(
                (app_dir / "app.bloomerp.toml").read_text(encoding="utf-8")
            )
        )
        project_result = Mock()

        # 2. Run aggregate sync with reusable operations isolated.
        with (
            patch(
                "bloomerp.cli.sync.synchronize_local_app",
                return_value=app_manifest,
            ) as synchronize_app,
            patch(
                "bloomerp.cli.sync.synchronize_local_project",
                return_value=project_result,
            ) as synchronize_project,
            patch("bloomerp.cli.sync.echo_app_sync") as echo_app,
            patch("bloomerp.cli.sync.echo_project_sync") as echo_project,
        ):
            result = runner.invoke(main, ["sync"])

        # 3. Verify both reusable synchronization layers ran successfully.
        assert result.exit_code == 0, result.output
        synchronize_app.assert_called_once_with(app_dir.resolve())
        synchronize_project.assert_called_once_with(force=False)
        echo_app.assert_called_once_with(app_dir.resolve(), app_manifest)
        echo_project.assert_called_once_with(project_result)


def test_combined_remote_sync_accepts_an_app_link_without_project_state():
    """
    Use case: An app is linked while its containing project has no link state.
    Expected result: Aggregate remote sync pulls the app and skips the project.
    """
    runner = CliRunner()

    with runner.isolated_filesystem():
        # 1. Create a linked app without project link metadata.
        create_project()
        app_dir = create_app(linked=True)
        Path(".bloomerp/state.toml").unlink()
        app_manifest = BloomerpAppManifest.model_validate(
            tomllib.loads(
                (app_dir / "app.bloomerp.toml").read_text(encoding="utf-8")
            )
        )

        # 2. Pull aggregate remote state with the app operation isolated.
        with (
            patch(
                "bloomerp.cli.sync.synchronize_app_from_remote",
                return_value=app_manifest,
            ) as synchronize_app,
            patch("bloomerp.cli.sync.echo_app_sync"),
        ):
            result = runner.invoke(main, ["sync", "--from-remote"])

        # 3. Verify the linked app was accepted as the remote-sync prerequisite.
        assert result.exit_code == 0, result.output
        assert "Skipped remote project sync" in result.output
        synchronize_app.assert_called_once_with(app_dir.resolve())
