import json
import os
import subprocess
import sys
import zipfile
from importlib.metadata import version

from bloomerp.cli.main import main


from click.testing import CliRunner


import tomllib
from pathlib import Path
from unittest.mock import Mock, call, patch


@patch("bloomerp.cli.project.link.BloomerpCliClient")
def test_project_link_keeps_state_when_relink_is_cancelled(client_type: Mock):
    linked_response = Mock(status_code=200)
    linked_response.json.return_value = {
        "id": "project-1",
        "name": "Existing",
    }
    client_type.return_value.request.return_value = linked_response
    runner = CliRunner()

    with runner.isolated_filesystem():
        Path(".bloomerp").mkdir()
        Path(".bloomerp/state.toml").write_text(
            'project_id = "project-1"\n', encoding="utf-8"
        )

        result = runner.invoke(main, ["project", "link"], input="n\n")

        assert result.exit_code == 1
        assert tomllib.loads(
            Path(".bloomerp/state.toml").read_text(encoding="utf-8")
        ) == {"project_id": "project-1"}
        assert client_type.return_value.request.call_count == 1


@patch("bloomerp.cli.project.link.BloomerpCliClient")
def test_project_link_confirms_before_replacing_a_valid_link(client_type: Mock):
    linked_response = Mock(status_code=200)
    linked_response.json.return_value = {
        "id": "project-1",
        "name": "Existing",
        "domain_name": "existing",
    }
    projects_response = Mock()
    projects_response.json.return_value = [
        {"id": "project-2", "name": "Replacement", "domain_name": "replacement"}
    ]
    client_type.return_value.request.side_effect = [
        linked_response,
        projects_response,
    ]
    runner = CliRunner()

    with runner.isolated_filesystem():
        Path(".bloomerp").mkdir()
        Path(".bloomerp/state.toml").write_text(
            'project_id = "project-1"\n', encoding="utf-8"
        )

        result = runner.invoke(main, ["project", "link"], input="y\n1\n")

        assert result.exit_code == 0
        assert "already linked to Existing" in result.output
        assert "Are you sure you want to continue?" in result.output
        assert tomllib.loads(
            Path(".bloomerp/state.toml").read_text(encoding="utf-8")
        ) == {"project_id": "project-2"}
        assert client_type.return_value.request.call_args_list[0].args == (
            "GET",
            "/api/projects/project-1/?type=SELF_MANAGED_CLOUD",
        )
        assert client_type.return_value.request.call_args_list[0].kwargs == {
            "allow_not_found": True
        }


@patch("bloomerp.cli.project.link.BloomerpCliClient")
def test_project_link_lists_owned_projects_and_writes_selection(client_type: Mock):
    response = Mock()
    response.json.return_value = [
        {"id": "project-1", "name": "First", "domain_name": "first"},
        {"id": "project-2", "name": "Second", "domain_name": "second"},
    ]
    client_type.return_value.request.return_value = response
    runner = CliRunner()

    with runner.isolated_filesystem():
        project_root = Path.cwd()
        Path(".bloomerp").mkdir()
        Path(".bloomerp/state.toml").write_text("", encoding="utf-8")
        Path("apps/inventory").mkdir(parents=True)
        os.chdir("apps/inventory")

        result = runner.invoke(main, ["project", "link"], input="2\n")

        assert result.exit_code == 0
        assert "1. First" in result.output
        assert "2. Second" in result.output
        assert "3. Create a new project" in result.output
        assert "Linked this project to Second" in result.output
        assert tomllib.loads(
            (project_root / ".bloomerp/state.toml").read_text(encoding="utf-8")
        ) == {"project_id": "project-2"}
        client_type.return_value.request.assert_called_once_with(
            "GET", "/api/projects/?type=SELF_MANAGED_CLOUD"
        )


@patch("bloomerp.cli.project.link.BloomerpCliClient")
def test_project_link_can_create_from_manifest_when_one_project_exists(
    client_type: Mock,
):
    projects_response = Mock()
    projects_response.json.return_value = [
        {"id": "project-existing", "name": "Existing", "domain_name": "existing"}
    ]
    created_response = Mock()
    created_response.json.return_value = {
        "id": "project-created",
        "name": "Example",
        "domain_name": "example",
    }
    client = client_type.return_value
    client.request.side_effect = [projects_response, created_response]
    client.session.return_value = {"user": {"id": 42}}
    runner = CliRunner()

    with runner.isolated_filesystem():
        Path(".bloomerp").mkdir()
        Path(".bloomerp/state.toml").write_text("", encoding="utf-8")
        Path(".bloomerp/project.bloomerp.toml").write_text(
            '''name = "Example"
description = "Example project"

[environment]
required = ["DJANGO_SECRET_KEY"]
optional = []

[runtime]
bloomerp_version = "1.2.3"
python_version = "3.13"

[deployment]
server_location = "US_EAST"
''',
            encoding="utf-8",
        )

        result = runner.invoke(main, ["project", "link"], input="2\n")

        assert result.exit_code == 0
        assert "1. Existing" in result.output
        assert "2. Create a new project" in result.output
        assert "Created Example" in result.output
        assert "Linked this project to Example" in result.output
        assert tomllib.loads(
            Path(".bloomerp/state.toml").read_text(encoding="utf-8")
        ) == {"project_id": "project-created"}
        assert client.request.call_args_list == [
            call("GET", "/api/projects/?type=SELF_MANAGED_CLOUD"),
            call(
                "POST",
                "/api/projects/",
                json={
                    "name": "Example",
                    "description": "Example project",
                    "owner": 42,
                    "server_location": "US_EAST",
                    "bloomerp_version": "1.2.3",
                    "type": "SELF_MANAGED_CLOUD",
                },
            ),
        ]


@patch("bloomerp.cli.project._django.subprocess.run")
def test_project_migrate_does_not_sync_fields_after_failure(run_process: Mock):
    run_process.return_value.returncode = 2
    runner = CliRunner()

    with runner.isolated_filesystem():
        Path(".bloomerp").mkdir()
        Path("manage.py").write_text("", encoding="utf-8")

        result = runner.invoke(main, ["project", "migrate"])

        assert result.exit_code == 2
        assert run_process.call_count == 1


@patch("bloomerp.cli.project._django.subprocess.run")
def test_project_migrate_syncs_application_fields_after_success(run_process: Mock):
    run_process.return_value.returncode = 0
    runner = CliRunner()

    with runner.isolated_filesystem():
        project_root = Path.cwd()
        manage_py = project_root / "manage.py"
        Path(".bloomerp").mkdir()
        manage_py.write_text("", encoding="utf-8")

        result = runner.invoke(main, ["project", "migrate", "--noinput"])

        assert result.exit_code == 0
        assert run_process.call_args_list == [
            call(
                [sys.executable, str(manage_py), "migrate", "--noinput"],
                cwd=project_root,
            ),
            call(
                [sys.executable, str(manage_py), "save_application_fields"],
                cwd=project_root,
            ),
        ]


@patch("bloomerp.cli.project._django.subprocess.run")
def test_project_makemigrations_wraps_django_command(run_process: Mock):
    run_process.return_value.returncode = 0
    runner = CliRunner()

    with runner.isolated_filesystem():
        project_root = Path.cwd()
        Path(".bloomerp").mkdir()
        Path("manage.py").write_text("", encoding="utf-8")

        result = runner.invoke(
            main,
            ["project", "makemigrations", "inventory", "--dry-run"],
        )

        assert result.exit_code == 0
        run_process.assert_called_once_with(
            [
                sys.executable,
                str(project_root / "manage.py"),
                "makemigrations",
                "inventory",
                "--dry-run",
            ],
            cwd=project_root,
        )


@patch("bloomerp.cli.project._django.subprocess.run")
def test_project_run_starts_django_from_project_root(run_process: Mock):
    run_process.return_value.returncode = 0
    runner = CliRunner()

    with runner.isolated_filesystem():
        project_root = Path.cwd()
        Path(".bloomerp").mkdir()
        Path("manage.py").write_text("", encoding="utf-8")
        Path("apps/inventory").mkdir(parents=True)
        os.chdir("apps/inventory")

        result = runner.invoke(
            main,
            ["project", "run", "0.0.0.0:9000", "--noreload"],
        )

        assert result.exit_code == 0
        run_process.assert_called_once_with(
            [
                sys.executable,
                str(project_root / "manage.py"),
                "runserver",
                "0.0.0.0:9000",
                "--noreload",
            ],
            cwd=project_root,
        )


def test_project_upload_requires_a_link_before_building():
    runner = CliRunner()

    with runner.isolated_filesystem():
        Path(".bloomerp").mkdir()
        Path(".bloomerp/state.toml").write_text("", encoding="utf-8")

        result = runner.invoke(main, ["project", "upload"])

        assert result.exit_code == 1
        assert "bloomerp project link" in result.output


@patch("bloomerp.cli.project.upload.BloomerpCliClient")
def test_project_upload_sends_manifest_and_existing_wheel(client_type: Mock):
    response = Mock()
    response.json.return_value = {
        "id": "snapshot-1",
        "snapshot_hash": "abc123",
        "created": True,
    }
    client_type.return_value.request.return_value = response
    runner = CliRunner()

    with runner.isolated_filesystem():
        Path(".bloomerp").mkdir()
        Path(".bloomerp/state.toml").write_text(
            'project_id = "project-1"\n', encoding="utf-8"
        )
        Path(".bloomerp/project.bloomerp.toml").write_text(
            """name = "Example"
description = "Demo"

[environment]
required = ["DJANGO_SECRET_KEY"]
optional = []

[runtime]
bloomerp_version = "1.13.1"
python_version = "3.13"
""",
            encoding="utf-8",
        )
        wheel = Path("example.whl")
        wheel.write_bytes(b"wheel bytes")

        result = runner.invoke(
            main,
            ["project", "upload", "--wheel", str(wheel)],
        )

        assert result.exit_code == 0
        assert "Created project snapshot snapshot-1" in result.output
        request = client_type.return_value.request
        assert request.call_args.args == (
            "POST",
            "/api/projects/project-1/upload-from-cli/",
        )
        assert json.loads(request.call_args.kwargs["data"]["manifest"])["name"] == (
            "Example"
        )
        assert request.call_args.kwargs["files"]["wheel"][0] == "example.whl"
        assert request.call_args.kwargs["timeout"] == 300


def test_project_build_wheel_contains_project_package_data():
    runner = CliRunner()

    with runner.isolated_filesystem():
        init_result = runner.invoke(
            main,
            ["project", "init", "example", "--app", "inventory"],
            input="\n",
        )
        assert init_result.exit_code == 0, init_result.output

        project_root = Path("example").resolve()
        static_file = project_root / "apps/inventory/static/inventory/app.js"
        static_file.parent.mkdir(parents=True)
        static_file.write_text("console.log('inventory');\n", encoding="utf-8")

        previous_directory = Path.cwd()
        os.chdir(project_root)
        try:
            build_result = runner.invoke(main, ["project", "build"])
        finally:
            os.chdir(previous_directory)

        assert build_result.exit_code == 0, build_result.output
        wheels = list((project_root / "dist").glob("*.whl"))
        assert len(wheels) == 1
        with zipfile.ZipFile(wheels[0]) as wheel:
            members = set(wheel.namelist())

        assert "apps/inventory/app.bloomerp.toml" in members
        assert "apps/inventory/templates/sample_detail_view.html" in members
        assert "apps/inventory/static/inventory/app.js" in members


@patch("bloomerp.cli.project.build.assert_scaffold_current")
@patch("bloomerp.cli.project.build.get_project_manifest")
@patch("bloomerp.cli.project.build.subprocess.run")
def test_project_build_uses_clean_staging_directory_and_writes_dist(
    run: Mock,
    get_project_manifest: Mock,
    assert_scaffold_current: Mock,
):
    def create_wheel(command, check):
        assert check is True
        output_dir = Path(command[command.index("--outdir") + 1])
        output_dir.joinpath("example-0.1.0-py3-none-any.whl").write_bytes(b"wheel")

    run.side_effect = create_wheel
    runner = CliRunner()

    with runner.isolated_filesystem():
        Path(".bloomerp").mkdir()
        Path("pyproject.toml").write_text("[project]\n", encoding="utf-8")

        result = runner.invoke(main, ["project", "build"])

        assert result.exit_code == 0
        assert Path("dist/example-0.1.0-py3-none-any.whl").read_bytes() == b"wheel"
        assert "Built project wheel" in result.output
        assert_scaffold_current.assert_called_once()


def test_project_scaffold_sync_preserves_project_owned_files():
    runner = CliRunner()

    with runner.isolated_filesystem():
        init_result = runner.invoke(
            main,
            ["project", "init", "example"],
            input="\nn\n",
        )
        assert init_result.exit_code == 0

        project_root = Path("example").resolve()
        project_settings = project_root / "config/settings/common.py"
        environment_file = project_root / ".env"
        pyproject = project_root / "pyproject.toml"
        project_settings.write_text("CUSTOM_SETTING = 'kept'\n", encoding="utf-8")
        environment_file.write_text("SECRET=kept\n", encoding="utf-8")
        pyproject.write_text(
            pyproject.read_text(encoding="utf-8") + "\n# custom dependency config\n",
            encoding="utf-8",
        )

        previous_directory = Path.cwd()
        os.chdir(project_root)
        try:
            result = runner.invoke(main, ["project", "scaffold-sync"])
        finally:
            os.chdir(previous_directory)

        assert result.exit_code == 0
        assert project_settings.read_text(encoding="utf-8") == "CUSTOM_SETTING = 'kept'\n"
        assert environment_file.read_text(encoding="utf-8") == "SECRET=kept\n"
        assert "# custom dependency config" in pyproject.read_text(encoding="utf-8")


def test_project_scaffold_sync_refuses_modified_generated_file_without_force():
    runner = CliRunner()

    with runner.isolated_filesystem():
        init_result = runner.invoke(
            main,
            ["project", "init", "example"],
            input="\nn\n",
        )
        assert init_result.exit_code == 0

        project_root = Path("example").resolve()
        generated_settings = project_root / "config/settings/generated/common.py"
        generated_settings.write_text("CUSTOM = True\n", encoding="utf-8")

        previous_directory = Path.cwd()
        os.chdir(project_root)
        try:
            refused = runner.invoke(main, ["project", "scaffold-sync"])
            assert generated_settings.read_text(encoding="utf-8") == "CUSTOM = True\n"
            forced = runner.invoke(main, ["project", "scaffold-sync", "--force"])
        finally:
            os.chdir(previous_directory)

        assert refused.exit_code == 1
        assert "Generated scaffold files contain local changes" in refused.output
        assert forced.exit_code == 0
        assert generated_settings.read_text(encoding="utf-8") != "CUSTOM = True\n"
        assert "backed up" in forced.output
        backups = list(
            project_root.glob(
                ".bloomerp/scaffold-backups/*/config/settings/generated/common.py"
            )
        )
        assert len(backups) == 1
        assert backups[0].read_text(encoding="utf-8") == "CUSTOM = True\n"


def test_project_scaffold_sync_check_reports_current_and_stale_json():
    runner = CliRunner()

    with runner.isolated_filesystem():
        init_result = runner.invoke(
            main,
            ["project", "init", "example"],
            input="\nn\n",
        )
        assert init_result.exit_code == 0

        project_root = Path("example").resolve()
        previous_directory = Path.cwd()
        os.chdir(project_root)
        try:
            current = runner.invoke(
                main,
                ["project", "scaffold-sync", "--check", "--output", "json"],
            )
            Path("config/settings/generated/common.py").write_text(
                "CUSTOM = True\n",
                encoding="utf-8",
            )
            stale = runner.invoke(
                main,
                ["project", "scaffold-sync", "--check", "--output", "json"],
            )
        finally:
            os.chdir(previous_directory)

        assert current.exit_code == 0
        assert json.loads(current.output) == {
            "contract_version": 1,
            "drift": [],
            "status": "current",
        }
        assert stale.exit_code == 1
        stale_payload = json.loads(stale.output)
        assert stale_payload["status"] == "stale"
        assert "config/settings/generated/common.py" in stale_payload["drift"]


def test_generated_project_passes_django_system_check():
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(
            main,
            ["project", "init", "example"],
            input="\nn\n",
        )
        assert result.exit_code == 0

        completed = subprocess.run(
            [sys.executable, "manage.py", "check"],
            cwd=Path("example"),
            capture_output=True,
            text=True,
            check=False,
        )

        assert completed.returncode == 0, completed.stdout + completed.stderr


def test_generated_project_production_runtime_entrypoints_load():
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(
            main,
            ["project", "init", "example"],
            input="\nn\n",
        )
        assert result.exit_code == 0

        # This test exercises production settings and runtime entrypoints using
        # the Bloomerp development environment, which need not install the
        # PostgreSQL driver declared by the generated project's pyproject.toml.
        Path("example/config/settings/production.py").write_text(
            "DATABASES = {\n"
            "    'default': {\n"
            "        'ENGINE': 'django.db.backends.sqlite3',\n"
            "        'NAME': ':memory:',\n"
            "    },\n"
            "}\n",
            encoding="utf-8",
        )

        environment = {
            **os.environ,
            "BLOOMERP_SETTINGS_ENV": "production",
            "BLOOMERP_PROJECT_ROOT": str(Path("example").resolve()),
            "DJANGO_SECRET_KEY": "test-secret",
            "DJANGO_ALLOWED_HOSTS": "example.test",
            "DJANGO_CSRF_TRUSTED_ORIGINS": "https://example.test",
            "POSTGRES_DB": "example",
            "POSTGRES_USER": "example",
            "POSTGRES_PASSWORD": "example",
            "POSTGRES_HOST": "postgres",
            "POSTGRES_PORT": "5432",
        }
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import config.asgi, config.celery; "
                    "from django.urls import reverse; "
                    "print(reverse('healthcheck'))"
                ),
            ],
            cwd=Path("example"),
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

        assert completed.returncode == 0, completed.stdout + completed.stderr
        assert completed.stdout.strip() == "/health/"


def test_project_init_requires_directory_in_non_interactive_mode():
    result = CliRunner().invoke(main, ["project", "init", "--no-input"])

    assert result.exit_code == 1
    assert "DIRECTORY is required" in result.output


def test_project_init_does_not_duplicate_manifest_version_options():
    result = CliRunner().invoke(main, ["project", "init", "--help"])

    assert result.exit_code == 0
    assert "--python-version" not in result.output
    assert "--bloomerp-version" not in result.output
    
    

def test_project_init_creates_manifests_without_requiring_an_app():
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(main, ["project", "init", "example"], input="\nn\n")

        assert result.exit_code == 0
        assert "Created Bloomerp project" in result.output
        assert Path("example/manage.py").is_file()
        assert not Path("example/core").exists()

        project_manifest = tomllib.loads(
            Path("example/.bloomerp/project.bloomerp.toml").read_text(encoding="utf-8")
        )
        assert project_manifest["name"] == "example"
        assert project_manifest["environment"]["required"] == []
        assert project_manifest["runtime"]["bloomerp_version"]
        assert project_manifest["runtime"]["python_version"] in {"3.12", "3.13"}
        assert Path("example/.python-version").read_text(encoding="utf-8") == (
            f'{project_manifest["runtime"]["python_version"]}\n'
        )
        assert 'requires-python = ">=3.12,<3.14"' in Path(
            "example/pyproject.toml"
        ).read_text(encoding="utf-8")
        assert 'include = ["apps*", "config*"]' in Path(
            "example/pyproject.toml"
        ).read_text(encoding="utf-8")
        assert Path("example/.bloomerp/state.toml").read_text(encoding="utf-8") == ""
        assert Path("example/.bloomerp/scaffold.lock").is_file()
        assert Path("example/config/settings/generated/common.py").is_file()
        assert Path("example/config/celery.py").is_file()
        assert Path("example/config/routing.py").is_file()
        assert Path("example/config/project_routing.py").is_file()
        assert Path("example/config/settings/common.py").is_file()
        assert not Path("example/config/settings/bloomerp.py").exists()
        user_common_settings = Path("example/config/settings/common.py").read_text(
            encoding="utf-8"
        )
        generated_common_settings = Path(
            "example/config/settings/generated/common.py"
        ).read_text(encoding="utf-8")
        assert "BLOOMERP_CONFIG = BloomerpConfig()" in user_common_settings
        assert "BLOOMERP_CONFIG = BloomerpConfig()" not in generated_common_settings
        assert not Path("example/config/settings/base.py").exists()


def test_project_init_can_run_the_app_init_flow():
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(
            main,
            ["project", "init", "example"],
            input="\ny\ninventory\n",
        )

        assert result.exit_code == 0
        app_manifest = tomllib.loads(
            Path("example/apps/inventory/app.bloomerp.toml").read_text(
                encoding="utf-8"
            )
        )
        assert app_manifest == {
            "name": "inventory",
            "version": "0.1.0",
            "description": "",
            "tagline": "",
            "environment": {"required": [], "optional": []},
            "django": {"app_config": ""},
            "modules": [],
            "models": [],
            "routes": [],
        }
        project_manifest = tomllib.loads(
            Path("example/.bloomerp/project.bloomerp.toml").read_text(encoding="utf-8")
        )
        assert project_manifest["django"]["installed_apps"] == ["apps.inventory"]
        settings = Path(
            "example/config/settings/generated/project_registry.py"
        ).read_text(encoding="utf-8")
        assert "'apps.inventory'" in settings
        assert Path("example/apps/__init__.py").is_file()


def test_project_init_supports_manifest_driven_non_interactive_generation():
    runner = CliRunner()

    with runner.isolated_filesystem():
        generator_version = version("Bloomerp")
        manifest_path = Path("managed-project.bloomerp.toml")
        manifest_path.write_text(
            f'''name = "Managed Project"
description = ""

[environment]
required = ["DJANGO_SECRET_KEY"]
optional = []

[runtime]
bloomerp_version = "{generator_version}"
python_version = "3.12"

[django]
installed_apps = ["generated_apps.project_app"]
''',
            encoding="utf-8",
        )

        result = runner.invoke(
            main,
            [
                "project",
                "init",
                "managed-project",
                "--manifest",
                str(manifest_path),
                "--no-input",
                "--no-app",
                "--no-local-files",
                "--output",
                "json",
            ],
        )

        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["contract_version"] == 1
        assert payload["generator_version"] == generator_version
        assert payload["installed_apps"] == ["generated_apps.project_app"]
        assert Path("managed-project/manage.py").is_file()
        assert Path("managed-project/.bloomerp/project.bloomerp.toml").is_file()
        assert Path("managed-project/.bloomerp/scaffold.lock").is_file()
        assert not Path("managed-project/.bloomerp/state.toml").exists()
        assert not Path("managed-project/.env").exists()
        assert not Path("managed-project/.gitignore").exists()
        assert not Path("managed-project/.python-version").exists()
