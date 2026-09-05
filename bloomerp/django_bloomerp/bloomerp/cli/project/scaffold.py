from __future__ import annotations

import hashlib
import json
import shutil
import tomllib
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from pprint import pformat

import click

from ..base import BloomerpProjectManifest
from ..utils import get_project_manifest, get_project_metadata_dir


TEMPLATE_ROOT = Path(__file__).resolve().parent.parent / "template_project"
LOCK_RELATIVE_PATH = Path(".bloomerp/scaffold.lock")
GENERATED_PATHS = (
    Path("manage.py"),
    Path("config/__init__.py"),
    Path("config/asgi.py"),
    Path("config/celery.py"),
    Path("config/urls.py"),
    Path("config/wsgi.py"),
    Path("config/settings/__init__.py"),
    Path("config/settings/generated/__init__.py"),
    Path("config/settings/generated/common.py"),
    Path("config/settings/generated/local.py"),
    Path("config/settings/generated/production.py"),
    Path("config/settings/generated/project_manifest.py"),
    Path("config/settings/generated/project_registry.py"),
)
USER_PATHS = (
    Path("config/project_channels.py"),
    Path("config/project_urls.py"),
    Path("config/settings/common.py"),
    Path("config/settings/local.py"),
    Path("config/settings/production.py"),
)


def _generator_version() -> str:
    try:
        return version("Bloomerp")
    except PackageNotFoundError:
        return "unknown"


def _digest(contents: str) -> str:
    return hashlib.sha256(contents.encode("utf-8")).hexdigest()


def _render_generated_file(
    relative_path: Path,
    manifest: BloomerpProjectManifest,
) -> str:
    from .marketplace_sources import installed_apps
    contents = (TEMPLATE_ROOT / relative_path).read_text(encoding="utf-8")
    if relative_path == Path("config/settings/generated/project_registry.py"):
        contents = contents.replace(
            "__PROJECT_INSTALLED_APPS__",
            pformat(installed_apps(manifest), width=88, sort_dicts=False),
        )
    elif relative_path == Path("config/settings/generated/project_manifest.py"):
        contents = contents.replace(
            "__PROJECT_MANIFEST__",
            pformat(
                manifest.model_dump(mode="json", exclude_none=True),
                width=88,
                # TOML groups scalars before tables; key order is not configuration.
                sort_dicts=True,
            ),
        )
    return contents


def _render_scaffold(
    manifest: BloomerpProjectManifest,
) -> dict[Path, str]:
    return {
        relative_path: _render_generated_file(relative_path, manifest)
        for relative_path in GENERATED_PATHS
    }


def _read_recorded_hashes(lock_path: Path) -> dict[str, str]:
    try:
        data = tomllib.loads(lock_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, tomllib.TOMLDecodeError):
        return {}

    files = data.get("files", {})
    if not isinstance(files, dict):
        return {}
    return {str(path): str(file_hash) for path, file_hash in files.items()}


def _write_lock(lock_path: Path, hashes: dict[str, str]) -> None:
    lines = [
        "contract_version = 1",
        f"generator_version = {json.dumps(_generator_version())}",
        "",
        "[files]",
    ]
    lines.extend(
        f"{json.dumps(path)} = {json.dumps(file_hash)}"
        for path, file_hash in sorted(hashes.items())
    )
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _backup_files(project_root: Path, paths: list[Path]) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup_root = project_root / ".bloomerp" / "scaffold-backups" / timestamp
    for relative_path in paths:
        source = project_root / relative_path
        destination = backup_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return backup_root


def get_scaffold_drift(
    project_root: Path,
    manifest: BloomerpProjectManifest,
) -> list[Path]:
    """Return generated or required extension files needing synchronization."""

    project_root = project_root.resolve()
    rendered_files = _render_scaffold(manifest)
    drift = [
        relative_path
        for relative_path, desired_contents in rendered_files.items()
        if not (project_root / relative_path).is_file()
        or (project_root / relative_path).read_text(encoding="utf-8")
        != desired_contents
    ]
    drift.extend(
        relative_path
        for relative_path in USER_PATHS
        if not (project_root / relative_path).exists()
    )

    desired_hashes = {
        path.as_posix(): _digest(contents)
        for path, contents in rendered_files.items()
    }
    recorded_hashes = _read_recorded_hashes(project_root / LOCK_RELATIVE_PATH)
    if recorded_hashes != desired_hashes:
        drift.append(LOCK_RELATIVE_PATH)

    return sorted(set(drift), key=lambda path: path.as_posix())


def assert_scaffold_current(
    project_root: Path,
    manifest: BloomerpProjectManifest,
) -> None:
    """Fail when project-generated scaffold differs from current CLI output."""

    drift = get_scaffold_drift(project_root, manifest)
    if not drift:
        return

    formatted_paths = "\n".join(f"  - {path}" for path in drift)
    raise click.ClickException(
        "Project scaffold is not current:\n"
        f"{formatted_paths}\n"
        "Run 'bloomerp project sync' before building."
    )


def synchronize_scaffold(
    project_root: Path,
    manifest: BloomerpProjectManifest,
    *,
    force: bool = False,
) -> tuple[list[Path], list[Path], Path | None]:
    """Synchronize CLI-owned scaffold files without touching user-owned files."""

    project_root = project_root.resolve()
    lock_path = project_root / LOCK_RELATIVE_PATH
    recorded_hashes = _read_recorded_hashes(lock_path)
    rendered_files = _render_scaffold(manifest)

    conflicts: list[Path] = []
    for relative_path, desired_contents in rendered_files.items():
        target = project_root / relative_path
        if not target.is_file():
            continue

        current_contents = target.read_text(encoding="utf-8")
        if current_contents == desired_contents:
            continue

        recorded_hash = recorded_hashes.get(relative_path.as_posix())
        template_contents = (TEMPLATE_ROOT / relative_path).read_text(
            encoding="utf-8"
        )
        if recorded_hash is None and current_contents == template_contents:
            continue
        if recorded_hash is None or _digest(current_contents) != recorded_hash:
            conflicts.append(relative_path)

    if conflicts and not force:
        formatted_paths = "\n".join(f"  - {path}" for path in conflicts)
        raise click.ClickException(
            "Generated scaffold files contain local changes:\n"
            f"{formatted_paths}\n"
            "Move custom behavior into project-owned extension files, or rerun "
            "with --force to back up and replace these files."
        )

    backup_root = _backup_files(project_root, conflicts) if conflicts else None

    updated: list[Path] = []
    hashes: dict[str, str] = {}
    for relative_path, desired_contents in rendered_files.items():
        target = project_root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if (
            not target.is_file()
            or target.read_text(encoding="utf-8") != desired_contents
        ):
            target.write_text(desired_contents, encoding="utf-8")
            updated.append(relative_path)
        hashes[relative_path.as_posix()] = _digest(desired_contents)

    created_user_files: list[Path] = []
    for relative_path in USER_PATHS:
        target = project_root / relative_path
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(TEMPLATE_ROOT / relative_path, target)
        created_user_files.append(relative_path)

    _write_lock(lock_path, hashes)
    return updated, created_user_files, backup_root


