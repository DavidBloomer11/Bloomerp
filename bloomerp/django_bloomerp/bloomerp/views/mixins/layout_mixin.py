from abc import ABC, abstractmethod
from typing import Any, Callable, Optional, Self
from urllib.parse import urlencode
from bloomerp.models.base_bloomerp_model import FieldLayout, LayoutItem, LayoutRow
from dataclasses import dataclass
from bloomerp.utils.renderer import render_field
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext

@dataclass
class ChangeContext:
    owner_content_type_id: int
    owner_object_id: int | str
    target_content_type_id: int | None = None
    layout_mode: str | None = None

    @property
    def scope(self) -> dict[str, object]:
        scope: dict[str, object] = {}
        if self.target_content_type_id is not None:
            scope["target_content_type_id"] = self.target_content_type_id
        if self.layout_mode:
            scope["layout_mode"] = self.layout_mode
        return scope
    
    @property
    def available_items_url(self) -> str:
        return reverse(
            "components_available_layout_items",
            kwargs={
                "content_type_id": self.owner_content_type_id,
            }
        ) + ("?" + urlencode(self.scope) if self.scope else "")
        
    @property
    def render_item_url(self) -> str:
        return reverse(
            "components_render_layout_item",
            kwargs={
                "content_type_id": self.owner_content_type_id,
            }
        ) + ("?" + urlencode(self.scope) if self.scope else "")
    
    @property
    def save_url(self) -> str:
        url = reverse(
            "components_save_layout_object",
            kwargs={
                "content_type_id": self.owner_content_type_id,
                "object_id": self.owner_object_id,
            }
        )
        return url + ("?" + urlencode(self.scope) if self.scope else "")

    @property
    def item_settings_url(self) -> str:
        return reverse(
            "components_item_settings",
            kwargs={
                "content_type_id": self.owner_content_type_id,
                "object_id": self.owner_object_id,
            }
        ) + ("?" + urlencode(self.scope) if self.scope else "")


@dataclass(frozen=True)
class LayoutBinding:
    """Connect a persisted layout owner to the model whose fields it renders."""

    owner: models.Model
    target_content_type: ContentType
    layout_mode: str | None = None

    @property
    def owner_content_type(self) -> ContentType:
        return ContentType.objects.get_for_model(self.owner)

    @property
    def target_model(self) -> type[models.Model]:
        model = self.target_content_type.model_class()
        if model is None:
            raise ValueError("The target content type does not resolve to a model.")
        return model

    @property
    def layout(self) -> FieldLayout:
        return self.owner.layout_obj

    @property
    def change_context(self) -> ChangeContext | None:
        if self.owner.pk is None:
            return None
        return ChangeContext(
            owner_content_type_id=self.owner_content_type.pk,
            owner_object_id=self.owner.pk,
            target_content_type_id=self.target_content_type.pk,
            layout_mode=self.layout_mode,
        )
    
    
class LayoutMixin(ABC):
    template_name = "cotton/features/layout/container.html"
    
    ts_container_component = ""
    
    ts_item_component = ""
    
    layout : FieldLayout
    
    item_has_border : bool = False
    
    change_context : Optional[ChangeContext] = None

    can_change : bool = True
    
    init_edit:bool = False
    
    # Extractor funcs
    is_visible_extractor_func : Optional[Callable[[Self, LayoutItem], bool]] = None
    not_visible_content_extractor_func : Optional[Callable[[Self, LayoutItem], bool]] = None
    content_extractor_func : Optional[Callable[[Self, LayoutItem], str]] = None
    label_extractor_func : Optional[Callable[[Self, LayoutItem], str]] = None
    icon_extractor_func : Optional[Callable[[Self, LayoutItem], str]] = None
    edit_url_extractor_func : Optional[Callable[[Self, LayoutItem], str]] = None
    search_keywords_extractor_func : Optional[Callable[[Self, LayoutItem], str]] = None
    config_extractor_func : Optional[Callable[[Self, LayoutItem], dict]] = None
    extra_attrs_extractor_func : Optional[Callable[[Self, LayoutItem], dict]] = None
    
    def get_layout(self) -> FieldLayout | None:
        return self.layout    
    
    def get_transformed_layout(self) -> FieldLayout:
        layout = self.get_layout()
        
        if not layout:
            return FieldLayout(rows=[])
        
        if not any(
            (
                self.is_visible_extractor_func,
                self.content_extractor_func,
                self.label_extractor_func,
                self.icon_extractor_func,
                self.edit_url_extractor_func,
                self.search_keywords_extractor_func,
                self.item_has_border,
                self.ts_item_component,
            )
        ):
            return layout
        
        transformed_rows: list[LayoutRow] = []
        for row in layout.rows:
            transformed_items: list[LayoutItem] = []
            for source_item in row.items:
                item = source_item.model_copy(deep=True)
                item.is_visible = self.is_visible_extractor_func(item) if self.is_visible_extractor_func else item.is_visible
                item.label = self.label_extractor_func(item) if self.label_extractor_func else item.label
                item.extra_attrs = self.extra_attrs_extractor_func(item) if self.extra_attrs_extractor_func else item.extra_attrs
                if item.is_visible:
                    item.content = self.content_extractor_func(item) if self.content_extractor_func else item.content
                    item.icon = self.icon_extractor_func(item) if self.icon_extractor_func else item.icon
                    if self.edit_url_extractor_func:
                        item.edit_url = self.edit_url_extractor_func(item)
                    elif change_context := self.get_change_context():
                        item.edit_url = change_context.item_settings_url
                    item.search_keywords = self.search_keywords_extractor_func(item) if self.search_keywords_extractor_func else item.search_keywords
                    item.config = self.config_extractor_func(item) if self.config_extractor_func else item.config
                else:
                    item.content = self.not_visible_content_extractor_func(item) if self.not_visible_content_extractor_func else item.content
                
                item.border = self.item_has_border
                item.component_name = self.ts_item_component
                transformed_items.append(item)

            transformed_rows.append(
                LayoutRow(
                    columns=row.columns,
                    title=gettext(row.title) if row.title else row.title,
                    items=transformed_items,
                )
            )
        
        return FieldLayout(rows=transformed_rows)
                
    def get_change_context(self) -> ChangeContext:
        return self.change_context
    
    def get_can_change(self):
        return self.can_change

    def get_layout_container_extra_attrs(self) -> dict[str, object]:
        return {}
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["layout"] = self.get_transformed_layout()
        
        # Get the change context
        ctx["change_context"] = self.get_change_context()
        ctx["can_change"] = self.get_can_change()
        ctx["layout_container_extra_attrs"] = self.get_layout_container_extra_attrs()
        
        # Components
        ctx["ts_container_component"] = self.ts_container_component
        ctx["ts_item_component"] = self.ts_item_component
        
        return ctx
    
    

    
    
    
    
    
    
