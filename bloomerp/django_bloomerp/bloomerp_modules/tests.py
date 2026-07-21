import uuid

from django.test import TestCase

from bloomerp_modules.models import Employee


class DynamicModelStringRepresentationTests(TestCase):
    def test_string_representation_does_not_load_unreferenced_relations(self):
        employee = Employee(
            first_name="Ada",
            last_name="Lovelace",
            job_title_id=uuid.uuid4(),
            department_id=uuid.uuid4(),
            team_id=uuid.uuid4(),
            office_location_id=uuid.uuid4(),
            cost_center_id=uuid.uuid4(),
        )

        with self.assertNumQueries(0):
            self.assertEqual(str(employee), "Ada Lovelace")
