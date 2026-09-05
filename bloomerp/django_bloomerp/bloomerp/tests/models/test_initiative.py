from django.core.exceptions import ValidationError

from bloomerp.models.project_management import Initiative, InitiativeStatus, Todo
from bloomerp.models.project_management.todo import TodoStatus
from bloomerp.tests.base import BaseBloomerpTestCaseWithModels


class TestInitiative(BaseBloomerpTestCaseWithModels):
    auto_create_customers = False

    def test_initiative_todo_count(self):
        """
        Use case: A project-management initiative has multiple to-dos assigned.
        Expected result: The initiative exposes the number of assigned to-dos.
        """
        # 1. Create an initiative.
        initiative = Initiative.objects.create(name="Launch customer portal")

        # 2. Create two to-dos assigned to the initiative and one unrelated to-do.
        Todo.objects.create(title="Design flow", initiative=initiative)
        Todo.objects.create(title="Build flow", initiative=initiative)
        Todo.objects.create(title="Unrelated work")

        # 3. Check that only assigned to-dos are counted.
        self.assertEqual(initiative.todo_count, 2)

    def test_initiative_completion_percentage_counts_finished_todos(self):
        """
        Use case: An initiative has completed, duplicate, cancelled, and open to-dos.
        Expected result: The initiative returns the finished to-do percentage as a string.
        """
        # 1. Create an initiative.
        initiative = Initiative.objects.create(name="Launch customer portal")

        # 2. Create finished and unfinished to-dos assigned to the initiative.
        Todo.objects.create(title="Done", initiative=initiative, status=TodoStatus.COMPLETED)
        Todo.objects.create(title="Duplicate", initiative=initiative, status=TodoStatus.DUPLICATE)
        Todo.objects.create(title="Cancelled", initiative=initiative, status=TodoStatus.CANCELLED)
        Todo.objects.create(title="In progress", initiative=initiative, status=TodoStatus.IN_PROGRESS)
        Todo.objects.create(title="Backlog", initiative=initiative, status=TodoStatus.BACKLOG)
        Todo.objects.create(title="Unrelated", status=TodoStatus.COMPLETED)

        # 3. Check that only assigned finished to-dos are included in the percentage.
        self.assertEqual(initiative.completion_percentage, "60%")

    def test_initiative_completion_percentage_returns_zero_without_todos(self):
        """
        Use case: An initiative has no assigned to-dos.
        Expected result: The initiative returns zero completion and has not started.
        """
        # 1. Create an initiative without to-dos.
        initiative = Initiative.objects.create(name="Launch customer portal")

        # 2. Check that empty initiatives report default computed values.
        self.assertEqual(initiative.completion_percentage, "0%")
        self.assertFalse(initiative.has_started)

    def test_initiative_has_started_checks_active_todo_statuses(self):
        """
        Use case: An initiative has at least one to-do in a started status.
        Expected result: The initiative reports that work has started.
        """
        # 1. Create an initiative.
        initiative = Initiative.objects.create(name="Launch customer portal")

        # 2. Create assigned to-dos where one has moved into review.
        Todo.objects.create(title="Backlog", initiative=initiative, status=TodoStatus.BACKLOG)
        Todo.objects.create(title="Review", initiative=initiative, status=TodoStatus.IN_REVIEW)

        # 3. Check that in-progress workflow states count as started.
        self.assertTrue(initiative.has_started)

    def test_initiative_computed_todo_properties_share_cached_status_counts(self):
        """
        Use case: Multiple computed to-do properties are read from one initiative instance.
        Expected result: The status counts are queried once and reused.
        """
        # 1. Create an initiative with assigned to-dos.
        initiative = Initiative.objects.create(name="Launch customer portal")
        Todo.objects.create(title="Done", initiative=initiative, status=TodoStatus.COMPLETED)
        Todo.objects.create(title="Review", initiative=initiative, status=TodoStatus.IN_REVIEW)

        # 2. Read all computed properties from the same instance.
        with self.assertNumQueries(1):
            todo_count = initiative.todo_count
            completion_percentage = initiative.completion_percentage
            has_started = initiative.has_started

        # 3. Check that all properties used the cached status counts.
        self.assertEqual(todo_count, 2)
        self.assertEqual(completion_percentage, "50%")
        self.assertTrue(has_started)

    def test_initiative_auto_fills_completed_at_if_completed(self):
        """
        Use case: An initiative is saved with the completed status.
        Expected result: The completed timestamp is automatically set.
        """
        # 1. Create a completed initiative without a completed timestamp.
        initiative = Initiative.objects.create(
            name="Launch customer portal",
            status=InitiativeStatus.COMPLETED,
        )

        # 2. Check that the model filled the completed timestamp.
        self.assertIsNotNone(initiative.completed_at)

    def test_initiative_clears_completed_at_if_status_changed(self):
        """
        Use case: A completed initiative is moved back to another status.
        Expected result: The completed timestamp is cleared.
        """
        # 1. Create a completed initiative.
        initiative = Initiative.objects.create(
            name="Launch customer portal",
            status=InitiativeStatus.COMPLETED,
        )
        self.assertIsNotNone(initiative.completed_at)

        # 2. Change the initiative away from completed.
        initiative.status = InitiativeStatus.IN_PROGRESS
        initiative.save()

        # 3. Check that the completed timestamp was cleared.
        self.assertIsNone(initiative.completed_at)

    def test_initiative_rejects_self_as_parent(self):
        """
        Use case: A saved initiative is assigned to itself as its parent.
        Expected result: The hierarchy validation rejects the self-reference.
        """
        initiative = Initiative.objects.create(name="Launch customer portal")

        initiative.parent = initiative

        with self.assertRaises(ValidationError):
            initiative.save()

    def test_initiative_rejects_descendant_as_parent(self):
        """
        Use case: A parent initiative is assigned one of its descendants as parent.
        Expected result: The hierarchy validation rejects the cycle.
        """
        initiative = Initiative.objects.create(name="Launch customer portal")
        child = Initiative.objects.create(name="Build portal", parent=initiative)
        descendant = Initiative.objects.create(name="Design portal", parent=child)

        initiative.parent = descendant

        with self.assertRaises(ValidationError):
            initiative.save()
