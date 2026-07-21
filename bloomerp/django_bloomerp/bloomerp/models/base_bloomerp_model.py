import json
from enum import Enum

from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from pydantic import BaseModel, Field
from typing import Optional

from typing import Callable, Optional
from bloomerp.models.mixins.absolute_url_model_mixin import AbsoluteUrlModelMixin
from bloomerp.models.mixins.avatar_model_mixin import AvatarModelMixin
from bloomerp.models.mixins.string_search_model_mixin import StringSearchModelMixin
from bloomerp.models.mixins.timestamp_model_mixin import TimestampModelMixin
from bloomerp.models.mixins.user_stamp_model_mixin import UserStampModelMixin
from bloomerp.models.mixins.uuid_model_mixin import UuidModelMixin
from bloomerp.permissions.definition import BloomerpPermission


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


class FieldLayout(BaseModel):
    rows: list[LayoutRow] = Field(default_factory=list)

class BloomerpModel(
    UuidModelMixin,
    TimestampModelMixin,
    StringSearchModelMixin,
    UserStampModelMixin,
    AbsoluteUrlModelMixin,
    AvatarModelMixin,
    models.Model,
):
    class Meta:
        abstract = True
        default_permissions = BloomerpPermission.to_tuple()
    
    files = GenericRelation("bloomerp.File")
    comments = GenericRelation("bloomerp.Comment")

    field_layout:Optional[FieldLayout] = None # DEPR
    form_layout:dict = None # DEPR 



    
