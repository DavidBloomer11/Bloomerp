from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any, Iterable

from django.db.models import Max, Min, QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from bloomerp.models.application_field import ApplicationField
from bloomerp.services.permission_services import UserPermissionManager, create_permission_str

from .base import BaseDataviewRenderer, DataviewPagination, DataviewRenderState


class GantDataviewRenderer(BaseDataviewRenderer):
    """Render records as rows on a horizontally scaled Gantt timeline."""

    template_name = "cotton/features/dataviews/gant.html"
    reserved_query_params = {"gant_page"}

    @classmethod
    def paginate_queryset(
        cls,
        queryset: QuerySet,
        preference,
        request: HttpRequest,
        options: object | None = None,
    ) -> DataviewPagination:
        """Paginate Gantt rows for intersection-triggered incremental loading."""
        start_field = cls._configured_field(
            preference,
            request,
            getattr(options, "start_field_id", None),
        )
        if start_field is not None:
            queryset = queryset.order_by(start_field.field, "pk")

        page_size = int(getattr(options, "page_size", 25))
        page_obj = cls.paginate_object_list(
            queryset,
            page_size,
            request.GET.get("gant_page", 1),
        )
        return DataviewPagination(queryset=page_obj, page_obj=page_obj)

    def get_context_data(self, pagination: DataviewPagination) -> dict[str, Any]:
        context = super().get_context_data(pagination)
        context.update(self._build_gant_context(pagination.queryset))
        return context

    def _build_gant_context(self, objects: Iterable) -> dict[str, Any]:
        start_field = self.get_field_from_data_view_fields(
            self.state.fields,
            getattr(self.options, "start_field_id", None),
        )
        end_field = self.get_field_from_data_view_fields(
            self.state.fields,
            getattr(self.options, "end_field_id", None),
        )
        dependency_from_field = self._get_self_relation_field(
            getattr(self.options, "dependency_from_field_id", None),
        )
        dependency_for_field = self._get_self_relation_field(
            getattr(self.options, "dependency_for_field_id", None),
        )

        context: dict[str, Any] = {
            "gant_configured": bool(start_field and end_field),
            "gant_rows": [],
            "gant_start": None,
            "gant_end": None,
            "gant_start_ms": None,
            "gant_end_ms": None,
            "gant_page_querystring": self.build_querystring(
                self.state.request,
                ("page", "gant_page"),
            ),
        }
        if not start_field or not end_field:
            return context

        timeline_start, timeline_end = self._get_timeline_range(
            self.state.queryset,
            start_field,
            end_field,
        )

        context.update({
            "gant_start": timeline_start,
            "gant_end": timeline_end,
            "gant_start_ms": self._to_milliseconds(timeline_start),
            "gant_end_ms": self._to_milliseconds(timeline_end),
            "gant_rows": [
                self._build_row(
                    obj,
                    start_field,
                    end_field,
                    dependency_from_field,
                    dependency_for_field,
                )
                for obj in objects
            ],
        })
        return context

    @classmethod
    def handle_action(cls, action: str, request, state) -> HttpResponse:
        if action != "page":
            return super().handle_action(action, request, state)

        pagination = cls.paginate_queryset(
            state.queryset,
            state.preference,
            request,
            state.dataview_options,
        )
        renderer = cls(DataviewRenderState(
            request=request,
            content_type_id=state.content_type.id,
            content_type=state.content_type,
            model=state.model,
            preference=state.preference,
            queryset=state.queryset,
            fields=state.data_view_fields,
            render_fields=state.data_view_render_fields,
            avatar_field=state.avatar_field,
            options=state.dataview_options,
        ))
        context = renderer.get_context_data(pagination)
        context["page_obj"] = pagination.page_obj
        return render(request, "components/objects/dataview_gant_rows.html", context)

    def _get_self_relation_field(self, field_id):
        application_field = self.get_field_from_data_view_fields(self.state.fields, field_id)
        if application_field is None:
            return None
        if application_field.field_type not in {"ForeignKey", "OneToOneField"}:
            return None
        if application_field.related_model_id != application_field.content_type_id:
            return None
        return application_field

    @staticmethod
    def _configured_field(preference, request: HttpRequest, field_id):
        if field_id in (None, ""):
            return None
        try:
            application_field = preference.content_type.applicationfield_set.get(pk=int(field_id))
        except (TypeError, ValueError, ApplicationField.DoesNotExist):
            return None

        if application_field.field_type not in {"DateField", "DateTimeField"}:
            return None
        permission = create_permission_str(preference.content_type.model_class(), "view")
        if not UserPermissionManager(request.user).has_field_permission(application_field, permission):
            return None
        return application_field

    @classmethod
    def _get_timeline_range(
        cls,
        queryset: QuerySet,
        start_field: ApplicationField,
        end_field: ApplicationField,
    ) -> tuple[datetime, datetime]:
        bounds = queryset.aggregate(
            gant_start=Min(start_field.field),
            gant_end=Max(end_field.field),
        )
        timeline_start = cls._as_datetime(bounds["gant_start"])
        timeline_end = cls._as_datetime(
            bounds["gant_end"],
            end_of_date=end_field.field_type == "DateField",
        )
        now = timezone.localtime()

        if timeline_start is None and timeline_end is None:
            return now, now + timedelta(hours=1)
        if timeline_start is None:
            timeline_start = timeline_end
        if timeline_end is None:
            timeline_end = timeline_start
        if timeline_end < timeline_start:
            timeline_end = timeline_start
        return timeline_start, timeline_end

    @classmethod
    def _build_row(
        cls,
        obj,
        start_field: ApplicationField,
        end_field: ApplicationField,
        dependency_from_field,
        dependency_for_field,
    ) -> dict[str, Any]:
        start_value = getattr(obj, start_field.field, None)
        end_value = getattr(obj, end_field.field, None)
        item_start = cls._as_datetime(start_value)
        item_end = cls._as_datetime(
            end_value,
            end_of_date=end_field.field_type == "DateField",
        )
        scheduled = item_start is not None and item_end is not None

        if scheduled:
            if item_end < item_start:
                item_end = item_start

        return {
            "object": obj,
            "start": start_value,
            "end": end_value,
            "scheduled": scheduled,
            "start_ms": cls._to_milliseconds(item_start),
            "end_ms": cls._to_milliseconds(item_end),
            "shows_time": (
                start_field.field_type == "DateTimeField"
                or end_field.field_type == "DateTimeField"
            ),
            "dependency_from_id": cls._related_object_id(obj, dependency_from_field),
            "dependency_for_id": cls._related_object_id(obj, dependency_for_field),
        }

    @staticmethod
    def _related_object_id(obj, application_field) -> str:
        if application_field is None:
            return ""
        try:
            model_field = obj._meta.get_field(application_field.field)
        except Exception:
            return ""
        value = getattr(obj, model_field.attname, None)
        return "" if value is None else str(value)

    @staticmethod
    def _as_datetime(value, *, end_of_date: bool = False) -> datetime | None:
        """Normalize date values without discarding DateTimeField precision."""
        if isinstance(value, datetime):
            result = value
        elif isinstance(value, date):
            result = datetime.combine(value, time.min)
            if end_of_date:
                result += timedelta(days=1)
        else:
            return None

        if timezone.is_naive(result):
            result = timezone.make_aware(result, timezone.get_current_timezone())
        return result

    @staticmethod
    def _to_milliseconds(value: datetime | None) -> int | None:
        """Return a browser-friendly Unix timestamp in milliseconds."""
        if value is None:
            return None
        return round(value.timestamp() * 1000)
