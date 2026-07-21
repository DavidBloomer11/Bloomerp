from django.conf import settings
from django.db import models
from django.db.models import Count
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext as _

from bloomerp.models.base_bloomerp_model import BloomerpModel, FieldLayout, LayoutItem, LayoutRow
from bloomerp.models.definition import BloomerpModelConfig


class InitiativeStatus(models.TextChoices):
    BACKLOG = ("backlog", "Backlog")
    IN_PROGRESS = ("in_progress", "In Progress")
    ON_HOLD = ("on_hold", "On Hold")
    COMPLETED = ("completed", "Completed")
    CANCELED = ("canceled", "Canceled")


class Initiative(BloomerpModel):
    """
    Project-management initiative that groups related to-dos.
    """

    bloomerp_config = BloomerpModelConfig(
        module="misc",
        layout=FieldLayout(
            rows=[
                LayoutRow(
                    title="Details",
                    columns=4,
                    items=[
                        LayoutItem(id="name", colspan=2),
                        LayoutItem(id="status", colspan=1),
                        LayoutItem(id="owner", colspan=1),
                        LayoutItem(id="description", colspan=4),
                    ],
                ),
                LayoutRow(
                    title="Timeline",
                    columns=3,
                    items=[
                        LayoutItem(id="start_date", colspan=1),
                        LayoutItem(id="target_date", colspan=1),
                        LayoutItem(id="completed_at", colspan=1),
                    ],
                ),
                LayoutRow(
                    title="Labels",
                    columns=1,
                    items=[
                        LayoutItem(id="labels", colspan=1),
                    ],
                ),
                LayoutRow(
                    title="Todo's",
                    columns=1,
                    items=[
                        LayoutItem(
                            id="todos",
                            colspan=1,
                            config={"inline_fields": ["title", "status"]},
                        ),
                    ]
                ),
            ]
        ),
        string_search_fields=["name", "description"],
    )

    class Meta(BloomerpModel.Meta):
        managed = True
        db_table = "bloomerp_initiative"

    avatar = None

    status = models.CharField(
        max_length=20,
        choices=InitiativeStatus.choices,
        default=InitiativeStatus.BACKLOG,
    )
    name = models.CharField(max_length=255, help_text=_("The name of the initiative"))
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    target_date = models.DateField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="owned_initiatives",
    )
    labels = models.ManyToManyField(
        "bloomerp.TodoLabel",
        blank=True,
        related_name="initiatives",
        help_text=_("Labels assigned to the initiative"),
    )

    @cached_property
    def todo_status_counts(self) -> dict[str, int]:
        """Return assigned to-do counts grouped by status."""
        prefetched_todos = getattr(self, "_prefetched_objects_cache", {}).get("todos")
        if prefetched_todos is not None:
            counts = {}
            for todo in prefetched_todos:
                counts[todo.status] = counts.get(todo.status, 0) + 1
            return counts

        return {
            row["status"]: row["total"]
            for row in self.todos.values("status").annotate(total=Count("id"))
        }

    @property
    def todo_count(self) -> int:
        """Return the number of to-dos assigned to this initiative."""
        return sum(self.todo_status_counts.values())

    @property
    def completion_percentage(self) -> str:
        """Return the percentage of finished to-dos as a string."""
        from bloomerp.models.project_management.todo import TodoStatus

        total = self.todo_count
        if total == 0:
            return "0%"

        finished_total = sum(
            self.todo_status_counts.get(status, 0)
            for status in (
                TodoStatus.COMPLETED,
                TodoStatus.DUPLICATE,
                TodoStatus.CANCELLED,
            )
        )
        return f"{round((finished_total / total) * 100)}%"

    @property
    def has_started(self) -> bool:
        """Return whether any assigned to-do has started."""
        from bloomerp.models.project_management.todo import TodoStatus

        return any(
            self.todo_status_counts.get(status, 0) > 0
            for status in (
                TodoStatus.IN_PROGRESS,
                TodoStatus.IN_REVIEW,
                TodoStatus.COMPLETED,
            )
        )

    @property
    def is_completed(self) -> bool:
        """Return whether this initiative is marked completed."""
        return self.status == InitiativeStatus.COMPLETED

    def clean(self):
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        elif not self.is_completed:
            self.completed_at = None

        return super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name
