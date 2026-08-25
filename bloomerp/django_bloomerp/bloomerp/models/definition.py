import json
import inspect
import re
from tokenize import String
from typing import Any, Callable, Literal, Optional, Type
from urllib.parse import urlsplit

from django.http import HttpRequest, HttpResponse
from bloomerp.config.definition import BloomerpConfig
from bloomerp.dataviews.base import BaseDataView
from bloomerp.permissions.definition import AccessRule
from bloomerp.workspaces.base import BaseTileConfig
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializeAsAny,
    field_validator,
    model_validator,
)
from django.conf import settings
from django.db.models import Model

class LayoutItem(BaseModel):
    id: int | str
    colspan: int = 1
    config: dict = Field(default_factory=dict)

    icon: str | None = None
    label: Optional[str] = None
    is_visible: bool = True
    content: Optional[str] = None
    component_name: Optional[str] = None
    border: bool = False
    edit_url: Optional[str] = None
    search_keywords: Optional[str] = None
    extra_attrs: Optional[dict] = Field(default_factory=dict)

    @property
    def config_json(self) -> str:
        return json.dumps(self.config)

    def set_content(self, content: str):
        self.content = content

class LayoutRow(BaseModel):
    columns: int
    items: list[LayoutItem] = Field(default_factory=list)
    title: Optional[str] = None

class BaseLayout(BaseModel):
    """Base layout class for defining layouts in Bloomerp.

    This class serves as a base for other layout classes, providing common
    attributes and methods that can be extended or overridden by subclasses.
    """

    name: str = "Default"
    is_default: bool = True
    rows: list[LayoutRow] = Field(default_factory=list)

class FieldLayout(BaseLayout):
    pass

class WorkspaceLayout(BaseLayout):
    pass

# ----------------------------------
# DETAIL TABS CONFIGURATION
# ----------------------------------
DETAIL_TAB_TEMPLATE_ARGUMENT = re.compile(r"{{\s*([^{}]+?)\s*}}")

def validate_detail_tab_url(url: str) -> str:
    """Validate and normalize a declarative detail-tab URL template."""
    normalized = url.strip()
    if not normalized:
        raise ValueError("URL is required.")

    arguments = {
        argument.strip()
        for argument in DETAIL_TAB_TEMPLATE_ARGUMENT.findall(normalized)
    }
    if arguments - {"pk"}:
        raise ValueError("Only the {{pk}} placeholder is supported.")

    parsed = urlsplit(normalized)
    is_internal = (
        not parsed.scheme
        and not parsed.netloc
        and normalized.startswith("/")
    )
    is_external = parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    if not is_internal and not is_external:
        raise ValueError(
            "Enter an internal URL beginning with / or a complete http(s) URL."
        )
    return normalized

class DetailTab(BaseModel):
    """A declarative tab shown on a model's detail view."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    url: str | None = Field(default=None, min_length=1, max_length=2048)
    url_name: str | None = Field(default=None, min_length=1, max_length=255)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Name is required.")
        return normalized

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        return validate_detail_tab_url(value) if value is not None else None

    @field_validator("url_name")
    @classmethod
    def normalize_url_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("URL name is required.")
        return normalized

    @model_validator(mode="after")
    def validate_url_source(self) -> "DetailTab":
        if (self.url is None) == (self.url_name is None):
            raise ValueError("Provide exactly one of url or url_name.")
        return self

class DetailTabFolder(BaseModel):
    """A top-level folder containing declarative detail tabs."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    tabs: list[DetailTab] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Name is required.")
        return normalized

class DetailTabsConfiguration(BaseModel):
    """A collection of declarative tabs shown on a model's detail view."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(default="Default", min_length=1, max_length=255)
    tabs: list[DetailTab | DetailTabFolder] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Name is required.")
        return normalized

def validate_declarative_tile_configs(
    tiles: list[BaseTileConfig],
    *,
    owner: str,
) -> list[BaseTileConfig]:
    """Require stable, unique IDs for tiles declared in configuration."""
    seen_ids: set[str] = set()
    for tile in tiles:
        tile_id = (tile.id or "").strip()
        if not tile_id:
            raise ValueError(f"Every tile declared on {owner} must have an id.")
        if tile_id in seen_ids:
            raise ValueError(f"Duplicate tile id '{tile_id}' declared on {owner}.")
        tile.id = tile_id
        seen_ids.add(tile_id)
    return tiles

class ApiNesting(BaseModel):
    for_field: str
    fields: list[str | Literal["__all__"]] = Field(default_factory=lambda: ["__all__"])
    on_action: list[Literal["list", "read"]] = Field(
        default_factory=lambda: ["list", "read"]
    )
    auto_pk: bool = True

    def get_accessible_fields(self, action: str) -> set[str] | None:
        normalized_action = str(action or "").strip().lower()
        if normalized_action not in self.on_action:
            return set()

        if "__all__" in self.fields:
            return None

        return {
            field_name
            for field_name in self.fields
            if field_name != "__all__"
        }

class ApiAccessSettings(BaseModel):
    """Declarative access granted outside a user's assigned policies."""

    anonymous: list[AccessRule] = Field(default_factory=list)
    authenticated: list[AccessRule] = Field(default_factory=list)
    inherit_anonymous_for_authenticated: bool = True

class ApiSettings(BaseModel):
    """
    Configures how Bloomerp API's are set up.

    Settings are:
        - enable_auto_generation: defines whether API endpoints are autogenerated for this model. Defaults to False
        - access: declarative anonymous and authenticated access rules
    """

    enable_auto_generation: bool = False
    access: ApiAccessSettings = Field(default_factory=ApiAccessSettings)
    nesting: list[ApiNesting] = Field(default_factory=list)

    def get_access_rules(self, *, authenticated: bool) -> list[AccessRule]:
        if not authenticated:
            return list(self.access.anonymous)

        rules = list(self.access.authenticated)
        if self.access.inherit_anonymous_for_authenticated:
            rules.extend(self.access.anonymous)
        return rules

    def has_anonymous_access(self) -> bool:
        return bool(self.access.anonymous)

    def has_authenticated_access(self) -> bool:
        return bool(self.access.authenticated)

    def get_nesting_rules(self, action: str) -> list[ApiNesting]:
        normalized_action = str(action or "").strip().lower()
        return [
            rule
            for rule in self.nesting
            if normalized_action in rule.on_action
        ]

class ObjectHTML(BaseModel):
    template_name:str

    should_render_func:Callable[[HttpRequest, Model], bool] = lambda req, obj : True

class ObjectAction(BaseModel):
    id:str

    label:str

    execution_func:Callable[[HttpRequest, Model], HttpResponse]
    
    should_render_func:Callable[[HttpRequest, Model], bool] = lambda req, obj : True
    
    icon:Optional[str] = None
    
    style:Literal["primary", "secondary"] = "secondary"
    
    success_message:Optional[str] = None
    
class ObjectModalAction(BaseModel):
    id:str
    
    label:str
    
    endpoint:Callable[[Model], str]
    
    icon:Optional[str] = None
    
    style:Literal["primary", "secondary"] = "secondary"
    
    should_render_func:Callable[[HttpRequest, Model], bool] = lambda req, obj : True
    
    modal_title:Optional[str] = ""

    modal_size:Literal["sm", "md", "lg", "xl", "full"] = "md"

class DetailViewSettings(BaseModel):
    """Settings regarding detail views for a model.

    An empty ``tab_configurations`` list retains router-derived defaults. Each
    configured layout becomes a named preference, with the first one selected.
    """
    skip_views: Optional[list[str]] = Field(
        default=None,
        description="Optional list of view names to skip when generating the detail view router.",
    )

    layout : Optional[list[FieldLayout]] = Field(
        default=None,
        description="Optional layout configuration for the detail view."
    )

    tab_configurations: list[DetailTabsConfiguration] = Field(default_factory=list)

class ModelViewSettings(BaseModel):
    """Optional settings for a model's collection views."""

    skip_views: Optional[list[str]] = None

    default_dataviews: list[SerializeAsAny[BaseDataView]] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def validate_default_dataviews(self):
        """Require unique names and one selected setup when defaults exist."""
        if not self.default_dataviews:
            return self

        names = [data_view.name for data_view in self.default_dataviews]
        if len(names) != len(set(names)):
            raise ValueError("Default data view names must be unique.")

        default_count = sum(
            data_view.is_default for data_view in self.default_dataviews
        )
        if default_count != 1:
            raise ValueError(
                "Exactly one configured data view must have is_default=True."
            )
        return self

class StringSearchSettings(BaseModel):
    """Optional settings for a model's search functionality."""

    allow_global_search: bool = True

    string_search_fields: list[str] | None = None

class ActivityLogSettings(BaseModel):
    """Optional settings for a model's audit functionality."""

    enabled : bool = True

class BloomerpModelConfig(BaseModel):
    """
    Used to define certain bloomerp related meta data on a model. 

    Settings are:
        - module: the canonical module to which this model belongs.
        - layout: a layout object defining how the default CRUD layout for users is.
        - tiles: reusable tile configurations associated with this model.
        - string_search_fields: optional field paths used by the shared string search service.

    Usage
    ```python
    from bloomerp.models.definition import BloomerpModelConfig

    class Lorum(BloomerpModel):
        bloomerp_config = BloomerpModelConfig(
            ...
        )
    ``` 
    """
    module: str | type | None = None
    
    layout: Optional[FieldLayout] = None

    tiles: list[SerializeAsAny[BaseTileConfig]] = Field(
        default_factory=list,
        description="Optional list of reusable tile configurations associated with this model."
    )

    is_internal: bool = False

    api_settings: Optional[ApiSettings] = None
    
    create_redirect_url_func : Optional[Callable[[Model], str]] = None
    
    detail_view_settings : Optional[DetailViewSettings] = None
    
    model_view_settings : Optional[ModelViewSettings] = None 
    
    object_actions : Optional[list[ObjectAction | ObjectHTML | ObjectModalAction]] = None

    string_search_settings : StringSearchSettings = StringSearchSettings(allow_global_search=True)
    
    activity_log_settings : ActivityLogSettings = ActivityLogSettings(enabled=True)
    
    @field_validator("tiles")
    @classmethod
    def validate_tiles(
        cls,
        value: list[BaseTileConfig],
    ) -> list[BaseTileConfig]:
        return validate_declarative_tile_configs(
            value,
            owner=cls.__name__,
        )
    
    @field_validator("module", mode="before")
    @classmethod
    def normalize_module(cls, value: Any) -> str | None:
        if value in (None, ""):
            return None

        if isinstance(value, str):
            return value

        try:
            from bloomerp.modules.definition import BloomerpModule, ModuleConfig
        except Exception:
            return value

        if isinstance(value, ModuleConfig):
            return value.full_id or value.id

        if inspect.isclass(value):
            if issubclass(value, ModuleConfig):
                module = value()
                return module.full_id or module.id

            if issubclass(value, BloomerpModule):
                module = value.to_config()
                return module.full_id or module.id

        return value

    def get_api_access_rules(self, *, authenticated: bool) -> list[AccessRule]:
        if self.api_settings is None:
            return []
        return self.api_settings.get_access_rules(authenticated=authenticated)

    def has_anonymous_api_access(self) -> bool:
        if self.api_settings is None:
            return False
        return self.api_settings.has_anonymous_access()

    def has_authenticated_api_access(self) -> bool:
        if self.api_settings is None:
            return False
        return self.api_settings.has_authenticated_access()

    def get_nesting_rules(self, action: str):
        if self.api_settings is None:
            return []
        return self.api_settings.get_nesting_rules(action)

    def should_enable_api_auto_generation(self) -> bool:
        bloomerp_config : BloomerpConfig = getattr(settings, "BLOOMERP_CONFIG")

        if self.api_settings is None:
            # In this case, use the global setting to determine whether to auto generate API endpoints
            return bloomerp_config.auto_generate_api_endpoints
        
        return self.api_settings.enable_auto_generation

def get_model_config(model_or_object:Type[Model]|Model) -> BloomerpModelConfig | None:
    """Returns the bloomerp model config for a model or object (if it exists)

    Args:
        model_or_object (Type[Model] | Model): the model or object

    Returns:
        BloomerpModelConfig | None: the config object
    """
    # Get the model class from either a model class or an instance
    model_class = model_or_object if inspect.isclass(model_or_object) else type(model_or_object)
    
    # Check if the model has a bloomerp_config attribute
    if hasattr(model_class, 'bloomerp_config'):
        config = getattr(model_class, 'bloomerp_config')
        if isinstance(config, BloomerpModelConfig):
            return config
    
    return None
    
