from __future__ import annotations

from django.db.models import Count, ForeignKey, OneToOneField, Q
from django.http import HttpResponse
from django.shortcuts import render
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bloomerp.models.users.user_list_view_preference import UserListViewPreference

from .base import BaseDataviewRenderer
from bloomerp.services.related_value_services import get_allowed_related_queryset


KANBAN_EMPTY_COLUMN_VALUE = "__none__"
KANBAN_UNAVAILABLE_COLUMN_VALUE = "__unavailable__"
KANBAN_MAX_RELATED_COLUMNS = 50


class KanbanDataviewRenderer(BaseDataviewRenderer):
    template_name = "cotton/features/dataviews/kanban.html"
    reserved_query_params = {"kanban_page", "kanban_column"}

    def get_context_data(self, pagination) -> dict:
        context = super().get_context_data(pagination)
        group_by_field = self.get_group_by_field(
            self.state.fields,
            self.options,
        )
        page_size = getattr(self.options, "page_size", 25)
        kanban_groups = None
        kanban_too_many_groups = False
        if group_by_field:
            model_field = self._get_model_field(
                self.state.queryset,
                group_by_field.field,
            )
            if isinstance(model_field, (ForeignKey, OneToOneField)):
                kanban_too_many_groups = self.has_too_many_related_columns(
                    group_by_field,
                    self.state.request.user,
                )
            if not kanban_too_many_groups:
                kanban_groups = self.build_groups(
                    self.state.queryset,
                    group_by_field,
                    user=self.state.request.user,
                    preference=self.state.preference,
                    page_size=page_size,
                )

        context.update({
            "kanban_groups": kanban_groups,
            "kanban_too_many_groups": kanban_too_many_groups,
            "group_by_field": group_by_field,
            "kanban_page_querystring": self.build_page_querystring(self.state.request),
            "component_args" : {
                "data-group-by-field-id": getattr(self.options, "group_by_field_id", ""),
                "data-group-by-field" : group_by_field.field if group_by_field else "",
            }
        })
        return context

    @staticmethod
    def has_too_many_related_columns(group_by_field, user) -> bool:
        """Return whether eligible related destinations exceed the safe limit."""
        return (
            get_allowed_related_queryset(group_by_field, user)
            .order_by()
            .values("pk")
            .distinct()
            .count()
            > KANBAN_MAX_RELATED_COLUMNS
        )

    @classmethod
    def build_page_querystring(cls, request) -> str:
        return cls.build_querystring(request, ("page", "kanban_page", "kanban_column"))

    @classmethod
    def get_group_by_field(cls, dataview_fields, options):
        return cls.get_field_from_data_view_fields(
            dataview_fields,
            getattr(options, "group_by_field_id", None),
        )

    @classmethod
    def handle_action(cls, action: str, request, state) -> HttpResponse:
        if action != "column":
            return super().handle_action(action, request, state)

        group_by_field = cls.get_group_by_field(
            state.dataview_fields,
            state.dataview_options,
        )
        if not group_by_field:
            return HttpResponse("Kanban grouping is not configured.", status=400)

        column_value = request.GET.get("kanban_column")
        if not column_value:
            return HttpResponse("Missing kanban column.", status=400)

        group = cls.build_column_group(
            state.queryset,
            group_by_field,
            column_value,
            preference=state.preference,
            page_size=getattr(state.dataview_options, "page_size", 25),
            page_number=request.GET.get("kanban_page", 1),
            user=request.user,
        )
        if group is None:
            return HttpResponse("Kanban column not found.", status=404)

        return render(
            request,
            "components/objects/dataview_kanban_cards.html",
            {
                "content_type_id": state.content_type.id,
                "fields": state.dataview_render_fields,
                "avatar_field": state.avatar_field,
                "group": group,
                "kanban_page_querystring": cls.build_page_querystring(request),
            },
        )

    @classmethod
    def build_column_group(
        cls,
        queryset,
        group_by_field,
        column_value: str,
        preference=None,
        page_size: int | None = None,
        page_number=1,
        user=None,
    ) -> dict | None:
        field_name = group_by_field.field
        model_field = cls._get_model_field(queryset, field_name)
        value = cls._coerce_column_value(column_value, model_field)

        if value == KANBAN_UNAVAILABLE_COLUMN_VALUE:
            allowed_ids = get_allowed_related_queryset(
                group_by_field,
                user,
            ).values("pk")
            column_queryset = queryset.exclude(
                **{f"{field_name}__isnull": True}
            ).exclude(**{f"{field_name}__in": allowed_ids})
            item_count = column_queryset.count()
            if item_count == 0:
                return None
            return cls._build_group(
                KANBAN_UNAVAILABLE_COLUMN_VALUE,
                "Unavailable value",
                column_queryset,
                page_size,
                page_number,
                item_count=item_count,
                is_destination=False,
                hide_field_name=field_name,
            )

        if (
            value is not None
            and isinstance(model_field, (ForeignKey, OneToOneField))
            and not get_allowed_related_queryset(
                group_by_field,
                user,
            ).filter(pk=value).exists()
        ):
            return None

        column_queryset = cls._build_column_queryset(queryset, field_name, model_field, value, preference=preference)
        item_count = column_queryset.count()
        if item_count == 0 and value is not None:
            return None

        if value is None:
            label = "Unassigned"
        elif isinstance(model_field, (ForeignKey, OneToOneField)):
            label = cls._get_related_label(queryset, field_name, value)
        else:
            label = cls._get_choice_label(model_field, value)

        return cls._build_group(
            value,
            label,
            column_queryset,
            page_size,
            page_number,
            item_count=item_count,
        )

    @classmethod
    def build_groups(cls, queryset, group_by_field, user=None, preference=None, page_size: int | None = None, page_number=1) -> list[dict]:
        field_name = group_by_field.field
        model_field = cls._get_model_field(queryset, field_name)
        groups = []

        if isinstance(model_field, (ForeignKey, OneToOneField)):
            count_rows = list(
                queryset
                .values(field_name)
                .annotate(item_count=Count("pk"))
                .order_by(field_name)
            )
            counts_by_value = {
                row[field_name]: row["item_count"]
                for row in count_rows
            }

            if None in counts_by_value:
                items = cls._build_column_queryset(queryset, field_name, model_field, None, preference=preference)
                groups.append(cls._build_group(
                    None, "Unassigned", items, page_size, page_number,
                    item_count=counts_by_value[None]
                ))

            allowed_related = get_allowed_related_queryset(group_by_field, user)
            allowed_ids = []
            for related_obj in allowed_related:
                value = related_obj.pk
                allowed_ids.append(value)
                items = cls._build_column_queryset(
                    queryset, field_name, model_field, value, preference=preference
                )
                groups.append(cls._build_group(
                    value, str(related_obj), items, page_size, page_number,
                    item_count=counts_by_value.get(value, 0)
                ))

            unavailable_count = queryset.exclude(
                **{f"{field_name}__isnull": True}
            ).exclude(**{f"{field_name}__in": allowed_ids}).count()
            if unavailable_count:
                unavailable_items = queryset.exclude(
                    **{f"{field_name}__isnull": True}
                ).exclude(**{f"{field_name}__in": allowed_ids})
                groups.append(cls._build_group(
                    KANBAN_UNAVAILABLE_COLUMN_VALUE,
                    "Unavailable value",
                    unavailable_items,
                    page_size,
                    page_number,
                    item_count=unavailable_count,
                    is_destination=False,
                    hide_field_name=field_name,
                ))
        else:
            empty_count = queryset.filter(cls._build_empty_filter(field_name, model_field)).count()
            if empty_count:
                items = cls._build_column_queryset(queryset, field_name, model_field, None, preference=preference)
                groups.append(cls._build_group(
                    None, "Unassigned", items, page_size, page_number,
                    item_count=empty_count
                ))

            if model_field and getattr(model_field, "choices", None):
                seen_values = set()
                counts_by_value = {
                    row[field_name]: row["item_count"]
                    for row in (
                        queryset
                        .exclude(cls._build_empty_filter(field_name, model_field))
                        .values(field_name)
                        .annotate(item_count=Count("pk"))
                        .order_by(field_name)
                    )
                }

                for choice_value, choice_label in cls._iter_choices(model_field.choices):
                    if choice_value in (None, ""):
                        continue

                    choice_items = cls._build_column_queryset(queryset, field_name, model_field, choice_value, preference=preference)
                    groups.append(cls._build_group(
                        choice_value, str(choice_label), choice_items, page_size, page_number,
                        item_count=counts_by_value.get(choice_value, 0)
                    ))
                    seen_values.add(choice_value)

                for value, item_count in counts_by_value.items():
                    if value in seen_values:
                        continue
                    items = cls._build_column_queryset(queryset, field_name, model_field, value, preference=preference)
                    groups.append(cls._build_group(
                        value, str(value), items, page_size, page_number,
                        item_count=item_count
                    ))
            else:
                count_rows = (
                    queryset
                    .exclude(cls._build_empty_filter(field_name, model_field))
                    .values(field_name)
                    .annotate(item_count=Count("pk"))
                    .order_by(field_name)
                )
                for row in count_rows:
                    value = row[field_name]
                    items = cls._build_column_queryset(queryset, field_name, model_field, value, preference=preference)
                    groups.append(cls._build_group(
                        value, str(value), items, page_size, page_number,
                        item_count=row["item_count"]
                    ))

        return groups

    @staticmethod
    def _format_column_value(value) -> str:
        return KANBAN_EMPTY_COLUMN_VALUE if value in (None, "") else str(value)

    @staticmethod
    def _get_model_field(queryset, field_name: str):
        model = queryset.model
        if not hasattr(model, "_meta"):
            return None

        try:
            return model._meta.get_field(field_name)
        except Exception:
            return None

    @staticmethod
    def _iter_choices(choices):
        for choice_value, choice_label in choices:
            if isinstance(choice_label, (list, tuple)):
                for nested_value, nested_label in choice_label:
                    yield nested_value, nested_label
            else:
                yield choice_value, choice_label

    @classmethod
    def _field_allows_blank_string(cls, model_field) -> bool:
        return bool(
            model_field
            and getattr(model_field, "empty_strings_allowed", False)
            and not (getattr(model_field, "many_to_one", False) or getattr(model_field, "one_to_one", False))
        )

    @classmethod
    def _build_empty_filter(cls, field_name: str, model_field) -> Q:
        empty_filter = Q(**{f"{field_name}__isnull": True})
        if cls._field_allows_blank_string(model_field):
            empty_filter |= Q(**{field_name: ""})
        return empty_filter

    @classmethod
    def _coerce_column_value(cls, raw_value: str, model_field):
        if raw_value == KANBAN_EMPTY_COLUMN_VALUE:
            return None
        if raw_value == KANBAN_UNAVAILABLE_COLUMN_VALUE:
            return KANBAN_UNAVAILABLE_COLUMN_VALUE

        if model_field is None:
            return raw_value

        try:
            if getattr(model_field, "many_to_one", False) or getattr(model_field, "one_to_one", False):
                return model_field.target_field.to_python(raw_value)
            return model_field.to_python(raw_value)
        except Exception:
            return raw_value

    @classmethod
    def _get_choice_label(cls, model_field, value) -> str:
        if model_field and getattr(model_field, "choices", None):
            for choice_value, choice_label in cls._iter_choices(model_field.choices):
                if choice_value == value:
                    return str(choice_label)

        return str(value)

    @staticmethod
    def _get_related_label(queryset, field_name: str, value) -> str:
        related_obj = (
            queryset
            .filter(**{field_name: value})
            .select_related(field_name)
            .first()
        )
        if related_obj:
            related_value = getattr(related_obj, field_name, None)
            if related_value:
                return str(related_value)

        return f"ID: {value}"

    @classmethod
    def _build_column_queryset(cls, queryset, field_name: str, model_field, value, preference:UserListViewPreference=None):
        sort_field = (preference.options if preference else {}).get("kanban", {}).get("sort_field", None)
        sort_direction = (preference.options if preference else {}).get("kanban", {}).get("sort_direction", "asc")
        
        if value is None:
            queryset = queryset.filter(cls._build_empty_filter(field_name, model_field))
        else:
            queryset = queryset.filter(**{field_name: value})
        
        if sort_field:
            if sort_direction == "desc":
                sort_field = f"-{sort_field}"
            queryset = queryset.order_by(sort_field)
            print(f"Sorting kanban column by {sort_field}")
        
        return queryset

    @classmethod
    def _build_group(
        cls,
        value,
        label: str,
        items: list,
        page_size: int | None = None,
        page_number=1,
        item_count: int | None = None,
        is_destination: bool = True,
        hide_field_name: str | None = None,
    ) -> dict:
        total_count = item_count if item_count is not None else len(items)

        if page_size:
            page_obj = cls.paginate_object_list(items, page_size, page_number)
            visible_items = page_obj.object_list
        else:
            page_obj = None
            visible_items = items

        return {
            "value": value,
            "request_value": cls._format_column_value(value),
            "label": label,
            "items": visible_items,
            "count": total_count,
            "page_obj": page_obj,
            "has_next_page": page_obj.has_next() if page_obj else False,
            "next_page_number": page_obj.next_page_number() if page_obj and page_obj.has_next() else None,
            "is_destination": is_destination,
            "hide_field_name": hide_field_name,
        }
