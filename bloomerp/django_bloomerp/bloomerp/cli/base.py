import os
from typing import Literal
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

from bloomerp.config.definition import BloomerpConfig

DEFAULT_BLOOMERP_IO_URL = "https://system.bloomerp.io"
BLOOMERP_IO_URL = os.environ.get(
    "BLOOMERP_IO_URL",
    DEFAULT_BLOOMERP_IO_URL,
).rstrip("/")


class BloomerpRuntime(BaseModel):
    model_config = ConfigDict(extra="allow")

    dependencies: list[str] = Field(default_factory=list)
    bloomerp_version:str
    python_version:str="3.13"

class BloomerpEnvironment(BaseModel):
    model_config = ConfigDict(extra="allow")

    required:list[str] = Field(default_factory=list)
    optional:list[str] = Field(default_factory=list)


class BloomerpDjango(BaseModel):
    model_config = ConfigDict(extra="allow")

    installed_apps: list[str] = Field(default_factory=list)


class BloomerpProjectApp(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None

    id: UUID
    version: str | None = None


class BloomerpProjectManifest(BaseModel):
    """
    The manifest for a BloomERP project
    """
    model_config = ConfigDict(extra="allow")

    name : str
    description : str    
    environment: BloomerpEnvironment
    runtime: BloomerpRuntime
    django: BloomerpDjango = Field(default_factory=BloomerpDjango)
    bloomerp: BloomerpConfig = Field(default_factory=BloomerpConfig)
    schema_version: Literal[4] = 4
    apps: list[BloomerpProjectApp] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def upgrade_app_selections(cls, value):
        if isinstance(value, dict) and value.get("schema_version", 2) == 2:
            value = dict(value)
            derived = {item.get('manifest', {}).get('django', {}).get('app_config') for item in value.get('apps', []) if isinstance(item, dict)}
            django = dict(value.get('django', {}))
            django['installed_apps'] = [app for app in django.get('installed_apps', []) if app not in derived and app != 'project_app']
            value['django'] = django
            selections = value.pop("extensions", value.get("apps", []))
            if not isinstance(selections, list) or any(not isinstance(item, dict) or "id" not in item for item in selections):
                raise ValueError("App selections must be a list of objects with IDs.")
            value["apps"] = [{"id": item["id"], "version": item.get("version"), "name": item.get("name")}
                             for item in selections]
            value["schema_version"] = 3
        if isinstance(value, dict) and value.get("schema_version") in {3, 4}:
            value = dict(value)
            files = value.pop("project_files", {})
            if files and "dependencies" not in value.get("runtime", {}):
                import tomllib
                from packaging.requirements import Requirement
                source = tomllib.loads(files.get("pyproject.toml", ""))
                dependencies = source.get("project", {}).get("dependencies", [])
                value["runtime"] = {**value["runtime"], "dependencies": [dep for dep in dependencies if Requirement(dep).name.lower() != "bloomerp"]}
            value["schema_version"] = 4
        return value


class BloomerpAppDjango(BaseModel):
    app_config: str = ""


class BloomerpAppModule(BaseModel):
    id: str
    name: str
    description: str = ""


class BloomerpAppModel(BaseModel):
    name: str
    database_table: str


class BloomerpAppRoute(BaseModel):
    url: str
    name: str
    description: str


class BloomerpAppManifest(BaseModel):
    """
    The manifest for a BloomERP app.
    """

    # Basic information about the app
    name: str
    display_name: str | None = None
    version: str = "0.1.0"
    required_version: str | None = None
    description: str = ""
    tagline: str = Field(default_factory=str)

    # Environment variables & Django configuration
    environment: BloomerpEnvironment = Field(
        default_factory=lambda: BloomerpEnvironment(required=[], optional=[])
    )
    django: BloomerpAppDjango = Field(default_factory=BloomerpAppDjango)

    # App components
    modules: list[BloomerpAppModule] = Field(default_factory=list)
    models: list[BloomerpAppModel] = Field(default_factory=list)
    routes: list[BloomerpAppRoute] = Field(default_factory=list)


class BloomerpAppState(BaseModel):
    app_id: str = Field(default="", validation_alias=AliasChoices("app_id", "marketplace_app_id"))


class BloomerpProjectState(BaseModel):
    project_id:str = ""
    manifest_revision: str = ""
    dependency_ids: list[str] = Field(default_factory=list)
    excluded_app_ids: list[str] = Field(default_factory=list)
    snapshot_id: str = ""
    generated_wheel_sha256: str = ""
    generated_wheel_filename: str = ""
    
