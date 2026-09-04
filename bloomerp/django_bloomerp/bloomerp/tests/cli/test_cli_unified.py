import hashlib
import io
import json
from pathlib import Path
from unittest.mock import Mock, patch
import zipfile

import click
from click.testing import CliRunner
import pytest

from bloomerp.cli.project.remote import pull_project, verify_generated_artifact
from bloomerp.cli.project.deploy import deploy
from bloomerp.cli.utils import get_project_state


def export_bytes(*, corrupt=False, user_files=None):
    generated = b"test generated wheel"
    files = {"wheels/generated-1.0.0-py3-none-any.whl": generated}
    artifacts = [{"filename": "generated-1.0.0-py3-none-any.whl", "kind": "generated", "sha256": "bad" if corrupt else hashlib.sha256(generated).hexdigest()}]
    if user_files:
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            for name, content in user_files.items():
                archive.writestr(name, content)
        data = stream.getvalue()
        files["wheels/user-1.0.0-py3-none-any.whl"] = data
        artifacts.append({"filename": "user-1.0.0-py3-none-any.whl", "kind": "user", "sha256": hashlib.sha256(data).hexdigest()})
    files["project.json"] = json.dumps({"contract_version": 1, "snapshot_id": "snapshot-1", "manifest": {"name": "Example", "description": "Test", "environment": {}, "runtime": {"bloomerp_version": "1.15.0", "python_version": "3.12"}}, "artifacts": artifacts, "auth_user_model": "project_app.User", "marketplace_apps": []})
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return stream.getvalue()


def initialize():
    Path(".bloomerp").mkdir()
    Path(".bloomerp/state.toml").write_text('project_id = "project-1"\n')


def test_pull_pins_generated_artifact_and_restores_user_files():
    with CliRunner().isolated_filesystem(), patch("bloomerp.cli.project.remote.subprocess.run") as install:
        initialize()
        client = Mock()
        client.request.return_value.content = export_bytes(user_files={"apps/custom/models.py": "# user source"})
        manifest = pull_project(client, "project-1")
        assert get_project_state().snapshot_id == "snapshot-1"
        assert manifest.django.installed_apps == ["project_app"]
        assert manifest.django.auth_user_model == "project_app.User"
        assert Path("apps/custom/models.py").read_text() == "# user source"
        assert "Bloomerp==1.15.0" in install.call_args.args[0]
        verify_generated_artifact()


def test_pull_rejects_corrupt_artifact_before_installing():
    with CliRunner().isolated_filesystem(), patch("bloomerp.cli.project.remote.subprocess.run") as install:
        initialize()
        client = Mock()
        client.request.return_value.content = export_bytes(corrupt=True)
        with pytest.raises(click.ClickException, match="integrity"):
            pull_project(client, "project-1")
        install.assert_not_called()
        assert get_project_state().snapshot_id == ""


def test_pull_preserves_local_edits_until_explicit_force():
    with CliRunner().isolated_filesystem(), patch("bloomerp.cli.project.remote.subprocess.run"):
        initialize()
        Path("apps/custom").mkdir(parents=True)
        Path("apps/custom/models.py").write_text("local edit")
        client = Mock()
        client.request.return_value.content = export_bytes(user_files={"apps/custom/models.py": "remote source"})
        with pytest.raises(click.ClickException, match="Local file differs"):
            pull_project(client, "project-1")
        assert Path("apps/custom/models.py").read_text() == "local edit"
        pull_project(client, "project-1", force=True)
        assert Path(".bloomerp/pull-backups/snapshot-1/apps/custom/models.py").read_text() == "local edit"


def test_deploy_uses_uploaded_snapshot_and_reports_failure():
    with CliRunner().isolated_filesystem():
        initialize()
        with (patch("bloomerp.cli.project.deploy.verify_generated_artifact"),
              patch("bloomerp.cli.project.deploy.synchronize_local_project"),
              patch("bloomerp.cli.project.deploy.build_project_wheel", return_value=Path("example.whl")),
              patch("bloomerp.cli.project.deploy.upload_project_wheel", return_value={"id": "uploaded-id"}),
              patch("bloomerp.cli.project.deploy.BloomerpCliClient") as client):
            client.return_value.request.return_value.json.side_effect = [{"deployment_id": "deployment-1"}, {"status": "FAILED", "error_message": "Migration failed"}]
            result = CliRunner().invoke(deploy)
            assert result.exit_code == 1
            assert "Migration failed" in result.output
            assert client.return_value.request.call_args_list[0].kwargs["json"] == {"snapshot_id": "uploaded-id"}
