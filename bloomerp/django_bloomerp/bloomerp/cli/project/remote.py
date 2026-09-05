"""Pull immutable generated artifacts and recover user-owned project files."""
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import shutil
import sys
import zipfile

import click

from ..base import BloomerpProjectManifest
from ..utils import get_project_metadata_dir, get_project_state, write_project_state


def pull_project(client, project_id, *, force=False):
    response = client.request("GET", f"/api/projects/{project_id}/export/", timeout=900)
    metadata = get_project_metadata_dir()
    root = metadata.parent
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        if sum(i.file_size for i in archive.infolist()) > 300 * 1024 * 1024:
            raise click.ClickException("Project export exceeds 300 MiB.")
        payload = json.loads(archive.read("project.json"))
        if payload.get("contract_version") != 2:
            raise click.ClickException("Unsupported project export contract.")
        manifest = BloomerpProjectManifest.model_validate(payload["manifest"])
        wheels = []
        user_files = dict(payload["manifest"].get("project_files", {}))
        if set(user_files) - {"pyproject.toml", "README.md"}:
            raise click.ClickException("Unsupported project source file in export.")
        user_files = {name: content.encode("utf-8") for name, content in user_files.items()}
        generated = None
        for artifact in payload["artifacts"]:
            name = artifact["filename"]
            if PurePosixPath(name).name != name or not name.endswith(".whl") or "\\" in name:
                raise click.ClickException("Invalid exported wheel path.")
            contents = archive.read("wheels/" + name)
            if hashlib.sha256(contents).hexdigest() != artifact["sha256"]:
                raise click.ClickException("Exported wheel failed integrity verification.")
            if artifact["kind"] == "user":
                with zipfile.ZipFile(io.BytesIO(contents)) as user_archive:
                    if sum(i.file_size for i in user_archive.infolist()) > 100 * 1024 * 1024:
                        raise click.ClickException("Expanded user wheel exceeds 100 MiB.")
                    for item in user_archive.infolist():
                        path = PurePosixPath(item.filename)
                        if path.is_absolute() or ".." in path.parts or "\\" in item.filename:
                            raise click.ClickException("Invalid user wheel path.")
                        if path.parts and path.parts[0] in {"apps", "config"} and not item.is_dir():
                            if path.parts[:3] == ("config", "settings", "generated"):
                                continue
                            user_files[item.filename] = user_archive.read(item)
            wheels.append((name, contents))
            if artifact["kind"] == "generated":
                generated = artifact
        if generated is None:
            raise click.ClickException("Export contains no generated artifact.")
    from .marketplace_sources import write_release_cache
    write_release_cache(payload.get("app_releases", payload["manifest"].get("apps", [])))
    # Never silently overwrite user edits. --force explicitly keeps a backup.
    for name, contents in user_files.items():
        target = root / name
        if target.exists() and target.read_bytes() != contents:
            from .scaffold import TEMPLATE_ROOT
            template = TEMPLATE_ROOT / name
            untouched_template = template.is_file() and target.read_bytes() == template.read_bytes()
            if not force and not untouched_template:
                raise click.ClickException(f"Local file differs: {name}. Commit your work, then use --force to back up and replace it.")
            backup = metadata / "pull-backups" / payload["snapshot_id"] / name
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_bytes(target.read_bytes())
    wheel_dir = metadata / "wheels"
    wheel_dir.mkdir(exist_ok=True)
    for name, contents in wheels:
        (wheel_dir / name).write_bytes(contents)
    installer = (["uv", "pip", "install", "--python", sys.executable] if shutil.which("uv")
                 else [sys.executable, "-m", "pip", "install"])
    subprocess.run([*installer, "--reinstall" if shutil.which("uv") else "--force-reinstall",
                    f"Bloomerp=={manifest.runtime.bloomerp_version}",
                    *[str(wheel_dir / name) for name, _ in wheels]], check=True)
    for name, contents in user_files.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(contents)
    state = get_project_state()
    state.snapshot_id = payload["snapshot_id"]
    state.generated_wheel_filename = generated["filename"]
    state.generated_wheel_sha256 = generated["sha256"]
    write_project_state(state)
    manifest.django = manifest.django.model_copy(update={"generated_apps": ["project_app"]})
    return manifest


def verify_generated_artifact():
    state = get_project_state()
    if not state.snapshot_id:
        raise click.ClickException("Run bloomerp sync --from-remote before deploying.")
    root = get_project_metadata_dir().parent
    if (root / "project_app").exists() or (root / "generated_apps").exists():
        raise click.ClickException("project_app is immutable; remove local shadow packages and pull its generated wheel.")
    path = get_project_metadata_dir() / "wheels" / state.generated_wheel_filename
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != state.generated_wheel_sha256:
        raise click.ClickException("Generated artifact changed; run bloomerp sync --from-remote.")
