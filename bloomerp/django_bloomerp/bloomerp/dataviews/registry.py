from enum import Enum

from django.utils.translation import gettext_lazy as _

from bloomerp.dataviews.base import DataviewTypeDefinition
from bloomerp.dataviews.calendar.config import CALENDAR_OPTIONS, CalendarDataView
from bloomerp.dataviews.calendar.renderer import CalendarDataviewRenderer
from bloomerp.dataviews.card.config import CARD_OPTIONS, CardDataView
from bloomerp.dataviews.card.renderer import CardDataviewRenderer
from bloomerp.dataviews.gant.config import GANTT_OPTIONS, GanttDataView
from bloomerp.dataviews.gant.renderer import GantDataviewRenderer
from bloomerp.dataviews.kanban.config import KANBAN_OPTIONS, KanbanDataView
from bloomerp.dataviews.kanban.renderer import KanbanDataviewRenderer
from bloomerp.dataviews.pivot_table.config import (
    PIVOT_TABLE_OPTIONS,
    PivotTableDataView,
    PivotTableDataviewOptions,
)
from bloomerp.dataviews.pivot_table.renderer import PivotTableDataviewRenderer
from bloomerp.dataviews.table.config import TABLE_OPTIONS, TableDataView
from bloomerp.dataviews.table.renderer import TableDataviewRenderer


class DataviewType(Enum):
    TABLE = DataviewTypeDefinition(
        key="table",
        label=_("Table"),
        description=_("Displays records in a sortable table."),
        icon="fa fa-table",
        renderer_cls=TableDataviewRenderer,
        config_cls=TableDataView,
        opts=TABLE_OPTIONS,
    )
    KANBAN = DataviewTypeDefinition(
        key="kanban",
        label=_("Kanban"),
        description=_("Displays records as cards grouped into columns."),
        icon="fa fa-table-columns",
        renderer_cls=KanbanDataviewRenderer,
        config_cls=KanbanDataView,
        opts=KANBAN_OPTIONS,
    )
    CARD = DataviewTypeDefinition(
        key="card",
        label=_("Card"),
        description=_("Displays records in a card grid."),
        icon="fa fa-id-card",
        renderer_cls=CardDataviewRenderer,
        config_cls=CardDataView,
        opts=CARD_OPTIONS,
    )
    CALENDAR = DataviewTypeDefinition(
        key="calendar",
        label=_("Calendar"),
        description=_(
            "Displays records on a day, week, month, year, or list calendar."
        ),
        icon="fa fa-calendar",
        renderer_cls=CalendarDataviewRenderer,
        config_cls=CalendarDataView,
        opts=CALENDAR_OPTIONS,
    )
    GANT = DataviewTypeDefinition(
        key="gant",
        label=_("Gantt"),
        description=_("Displays records as a timeline."),
        icon="fa fa-chart-gantt",
        renderer_cls=GantDataviewRenderer,
        config_cls=GanttDataView,
        opts=GANTT_OPTIONS,
    )
    PIVOT_TABLE = DataviewTypeDefinition(
        key="pivot_table",
        label=_("Pivot"),
        description=_(
            "Summarizes records across selected row, column, and value fields."
        ),
        icon="fa fa-table-cells",
        renderer_cls=PivotTableDataviewRenderer,
        config_cls=PivotTableDataView,
        requires_display_fields=False,
        model=PivotTableDataviewOptions,
        opts=PIVOT_TABLE_OPTIONS,
    )

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        return [(item.value.key, item.value.label) for item in cls]

    @classmethod
    def values(cls) -> list[str]:
        return [item.value.key for item in cls]

    @classmethod
    def from_key(cls, key: str) -> DataviewTypeDefinition:
        for item in cls:
            if item.value.key == key:
                return item.value
        raise ValueError(f"Unsupported dataview type: {key}")
