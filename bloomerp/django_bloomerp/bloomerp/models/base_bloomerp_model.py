from django.utils.translation import gettext_lazy as _
import json
from enum import Enum

from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from typing import Optional

from bloomerp.models.definition import BaseLayout, FieldLayout, LayoutItem, LayoutRow
from bloomerp.models.mixins.absolute_url_model_mixin import AbsoluteUrlModelMixin
from bloomerp.models.mixins.avatar_model_mixin import AvatarModelMixin
from bloomerp.models.mixins.string_search_model_mixin import StringSearchModelMixin
from bloomerp.models.mixins.timestamp_model_mixin import TimestampModelMixin
from bloomerp.models.mixins.user_stamp_model_mixin import UserStampModelMixin
from bloomerp.models.mixins.uuid_model_mixin import UuidModelMixin
from bloomerp.permissions.definition import BloomerpPermission

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



    
