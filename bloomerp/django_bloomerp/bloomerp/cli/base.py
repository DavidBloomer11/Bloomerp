import os

from pydantic import BaseModel, ConfigDict, Field

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

class BloomerpDeploymentManifest(BaseModel):
    server_location:str = "EU_CENTRAL"


class BloomerpDjango(BaseModel):
    model_config = ConfigDict(extra="allow")

    installed_apps: list[str] = Field(default_factory=list)

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
    marketplace_app_id: str = ""


class BloomerpProjectState(BaseModel):
    project_id:str = ""
    
