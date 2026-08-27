import os
from typing import Optional
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

    required:list[str] = Field(default_factory=lambda: ["DJANGO_SECRET_KEY"])
    optional:list[str] = Field(default_factory=list)

class BloomerpDeploymentManifest(BaseModel):
    server_location:str = "EU_CENTRAL"


class BloomerpDjango(BaseModel):
    model_config = ConfigDict(extra="allow")

    installed_apps: list[str] = Field(default_factory=list)

class BloomerpProjectManifest(BaseModel):
    model_config = ConfigDict(extra="allow")

    name : str
    description : str    
    environment: BloomerpEnvironment
    runtime: BloomerpRuntime
    django: BloomerpDjango = Field(default_factory=BloomerpDjango)
    
    
class BloomerpAppManifest(BaseModel):
    name: str
    version: str = "0.1.0"
    description: str = ""

class BloomerpProjectState(BaseModel):
    project_id:str = ""
    
