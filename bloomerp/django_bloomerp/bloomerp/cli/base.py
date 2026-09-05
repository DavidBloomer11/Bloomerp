import os
from typing import Literal
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from bloomerp.config.definition import BloomerpConfig

DEFAULT_BLOOMERP_IO_URL = "http://127.0.0.1:8000"
BLOOMERP_IO_URL = os.environ.get(
    "BLOOMERP_IO_URL",
    DEFAULT_BLOOMERP_IO_URL,
).rstrip("/")


class BloomerpRuntime(BaseModel):
    model_config = ConfigDict(extra="allow")

    bloomerp_version:str
    python_version:str="3.13"

class BloomerpEnvironment(BaseModel):
    model_config = ConfigDict(extra="allow")

    required:list[str] = Field(default_factory=list)
    optional:list[str] = Field(default_factory=list)


class BloomerpDjango(BaseModel):
    model_config = ConfigDict(extra="allow")

    installed_apps: list[str] = Field(default_factory=list)


class BloomerpExtension(BaseModel):
    model_config = ConfigDict(extra="allow")

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
    extensions: list[BloomerpExtension] = Field(default_factory=list)
    schema_version: Literal[2] = 2
    project_files: dict[str, str] = Field(default_factory=dict)
    apps: list[dict] = Field(default_factory=list)


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
    snapshot_id: str = ""
    generated_wheel_sha256: str = ""
    generated_wheel_filename: str = ""
    
