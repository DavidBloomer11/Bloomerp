import os
import subprocess
import tomllib
from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from bloomerp.cli.base import (
    BloomerpEnvironment,
    BloomerpProjectManifest,
    BloomerpRuntime,
)
from bloomerp.cli.main import main
from bloomerp.cli.toml import write_toml_model


def create_project() -> tuple[Path, Path]:
    metadata_dir = Path(".bloomerp")
    metadata_dir.mkdir()
    manifest_path = metadata_dir / "project.bloomerp.toml"
    write_toml_model(
        manifest_path,
        BloomerpProjectManifest(
            name="Example",
            description="Upgrade test",
            environment=BloomerpEnvironment(),
            runtime=BloomerpRuntime(
                bloomerp_version="1.14.7",
                python_version="3.13",
            ),
        ),
    )
    pyproject_path = Path("pyproject.toml")
    pyproject_path.write_text(
        '''[project]
name = "example"
version = "0.1.0"
dependencies = [
    "Django>=5.1,<6",
    "Bloomerp>=1.14",
]

[tool.example]
preserved = true
''',
        encoding="utf-8",
    )
    return manifest_path, pyproject_path


def test_upgrade_explicit_version_updates_project_files_without_installing():
    """
    Use case: A user selects an exact Bloomerp version without --install.
    Expected result: Both declarations update while the environment stays untouched.
    """
    runner = CliRunner()

    with runner.isolated_filesystem():
        # 1. Create project metadata with an older dependency constraint.
        manifest_path, pyproject_path = create_project()

        # 2. Upgrade to an explicitly selected release.
        with patch("bloomerp.cli.upgrade.subprocess.run") as run:
            result = runner.invoke(main, ["upgrade", "1.15.0"])

        # 3. Verify both files and the non-installing default.
        assert result.exit_code == 0, result.output
        assert run.call_count == 0
        pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        assert pyproject["project"]["dependencies"] == [
            "Django>=5.1,<6",
            "Bloomerp==1.15.0",
        ]
        assert pyproject["tool"]["example"]["preserved"] is True
        manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["runtime"]["bloomerp_version"] == "1.15.0"
        assert "package manager" in result.output


def test_upgrade_without_version_uses_latest_pypi_release():
    """
    Use case: A user omits the target version.
    Expected result: The latest PyPI release is normalized and selected.
    """
    runner = CliRunner()
    response = Mock()
    response.json.return_value = {"info": {"version": "1.16.0"}}

    with runner.isolated_filesystem():
        # 1. Create project metadata.
        manifest_path, _pyproject_path = create_project()

        # 2. Resolve and apply the latest published release.
        with patch("bloomerp.cli.upgrade.requests.get", return_value=response) as get:
            result = runner.invoke(main, ["upgrade"])

        # 3. Verify PyPI lookup and the selected manifest version.
        assert result.exit_code == 0, result.output
        get.assert_called_once_with(
            "https://pypi.org/pypi/Bloomerp/json",
            timeout=30,
        )
        response.raise_for_status.assert_called_once_with()
        manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["runtime"]["bloomerp_version"] == "1.16.0"


def test_upgrade_install_targets_project_virtualenv_through_uv():
    """
    Use case: A project-local virtual environment exists and --install is requested.
    Expected result: uv installs the exact release into that interpreter.
    """
    runner = CliRunner()

    with runner.isolated_filesystem():
        # 1. Create project metadata and its local Python environment marker.
        create_project()
        python = Path(".venv/bin/python")
        python.parent.mkdir(parents=True)
        python.write_text("", encoding="utf-8")

        # 2. Upgrade and install through uv into the resolved interpreter.
        with (
            patch.dict(os.environ, {"VIRTUAL_ENV": ""}),
            patch("bloomerp.cli.upgrade.shutil.which", return_value="/usr/bin/uv"),
            patch("bloomerp.cli.upgrade.subprocess.run") as run,
        ):
            result = runner.invoke(main, ["upgrade", "1.15.0", "--install"])

        # 3. Verify the exact interpreter and release passed to the installer.
        assert result.exit_code == 0, result.output
        run.assert_called_once_with(
            [
                "/usr/bin/uv",
                "pip",
                "install",
                "--python",
                str(python.resolve()),
                "Bloomerp==1.15.0",
            ],
            cwd=Path.cwd(),
            check=True,
        )


def test_upgrade_install_preserves_virtualenv_python_symlink():
    """
    Use case: A uv virtualenv's Python points to uv's managed base interpreter.
    Expected result: Installation targets the virtualenv path, not the symlink target.
    """
    runner = CliRunner()

    with runner.isolated_filesystem():
        # 1. Create a project virtualenv linked to a managed Python installation.
        create_project()
        managed_python = Path("uv-managed/bin/python3.13").absolute()
        managed_python.parent.mkdir(parents=True)
        managed_python.write_text("", encoding="utf-8")
        virtualenv_python = Path(".venv/bin/python")
        virtualenv_python.parent.mkdir(parents=True)
        virtualenv_python.symlink_to(managed_python)

        # 2. Upgrade and install through uv using the project environment.
        with (
            patch.dict(os.environ, {"VIRTUAL_ENV": ""}),
            patch("bloomerp.cli.upgrade.shutil.which", return_value="/usr/bin/uv"),
            patch("bloomerp.cli.upgrade.subprocess.run") as run,
        ):
            result = runner.invoke(main, ["upgrade", "1.15.0", "--install"])

        # 3. Verify the virtualenv path was preserved instead of dereferenced.
        assert result.exit_code == 0, result.output
        run.assert_called_once_with(
            [
                "/usr/bin/uv",
                "pip",
                "install",
                "--python",
                str(virtualenv_python.absolute()),
                "Bloomerp==1.15.0",
            ],
            cwd=Path.cwd(),
            check=True,
        )


def test_upgrade_install_preserves_dependency_extras_and_marker():
    """
    Use case: The project's Bloomerp dependency declares extras and a marker.
    Expected result: Installation uses the complete rewritten requirement.
    """
    runner = CliRunner()

    with runner.isolated_filesystem():
        # 1. Create a project with optional Bloomerp dependencies and a target Python.
        _manifest_path, pyproject_path = create_project()
        pyproject_path.write_text(
            pyproject_path.read_text(encoding="utf-8").replace(
                "Bloomerp>=1.14",
                'Bloomerp[postgres]>=1.14; python_version >= \\"3.12\\"',
            ),
            encoding="utf-8",
        )
        python = Path(".venv/bin/python")
        python.parent.mkdir(parents=True)
        python.write_text("", encoding="utf-8")

        # 2. Upgrade and install the dependency through uv.
        with (
            patch.dict(os.environ, {"VIRTUAL_ENV": ""}),
            patch("bloomerp.cli.upgrade.shutil.which", return_value="/usr/bin/uv"),
            patch("bloomerp.cli.upgrade.subprocess.run") as run,
        ):
            result = runner.invoke(main, ["upgrade", "1.15.0", "--install"])

        # 3. Verify the installer and pyproject receive the same full requirement.
        requirement = 'Bloomerp[postgres]==1.15.0; python_version >= "3.12"'
        assert result.exit_code == 0, result.output
        run.assert_called_once_with(
            [
                "/usr/bin/uv",
                "pip",
                "install",
                "--python",
                str(python.resolve()),
                requirement,
            ],
            cwd=Path.cwd(),
            check=True,
        )
        dependencies = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))[
            "project"
        ]["dependencies"]
        assert requirement in dependencies


def test_upgrade_install_finds_windows_active_virtualenv():
    """
    Use case: An activated Windows virtualenv exposes Python under Scripts.
    Expected result: Installation targets that Python executable.
    """
    runner = CliRunner()

    with runner.isolated_filesystem():
        # 1. Create a project and a Windows-style active virtualenv interpreter.
        create_project()
        environment = Path("active-environment").resolve()
        python = environment / "Scripts" / "python.exe"
        python.parent.mkdir(parents=True)
        python.write_text("", encoding="utf-8")

        # 2. Upgrade while VIRTUAL_ENV points to the Windows-style environment.
        with (
            patch.dict(os.environ, {"VIRTUAL_ENV": str(environment)}),
            patch("bloomerp.cli.upgrade.shutil.which", return_value=None),
            patch("bloomerp.cli.upgrade.subprocess.run") as run,
        ):
            result = runner.invoke(main, ["upgrade", "1.15.0", "--install"])

        # 3. Verify the pip fallback targets Scripts/python.exe.
        assert result.exit_code == 0, result.output
        run.assert_called_once_with(
            [str(python), "-m", "pip", "install", "Bloomerp==1.15.0"],
            cwd=Path.cwd(),
            check=True,
        )


def test_upgrade_install_refuses_implicit_global_environment_before_writes():
    """
    Use case: Installation is requested without a virtualenv or explicit override.
    Expected result: The command fails without changing project declarations.
    """
    runner = CliRunner()

    with runner.isolated_filesystem():
        # 1. Create a project with no local environment and record its files.
        manifest_path, pyproject_path = create_project()
        original_manifest = manifest_path.read_text(encoding="utf-8")
        original_pyproject = pyproject_path.read_text(encoding="utf-8")

        # 2. Request installation without authorizing a target interpreter.
        with (
            patch.dict(os.environ, {"VIRTUAL_ENV": ""}),
            patch("bloomerp.cli.upgrade.subprocess.run") as run,
        ):
            result = runner.invoke(main, ["upgrade", "1.15.0", "--install"])

        # 3. Verify the safe failure occurred before installation or file writes.
        assert result.exit_code != 0
        assert "No project Python environment found" in result.output
        assert run.call_count == 0
        assert manifest_path.read_text(encoding="utf-8") == original_manifest
        assert pyproject_path.read_text(encoding="utf-8") == original_pyproject
