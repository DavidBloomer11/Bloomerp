



from django.test import SimpleTestCase

from bloomerp.filters.manager import QuerysetFilterManager


class TestFilterManager(SimpleTestCase):

    def test_strip_args(self):
        manager = QuerysetFilterManager()
        test_cases = [
            ("first_name", "David", [("first_name", "David")]),
            (
                "first_name",
                "David||first_name=James",
                [("first_name", "David"), ("first_name", "James")],
            ),
            (
                "first_name",
                "John||first_name=James||company__name=XYZ",
                [
                    ("first_name", "John"),
                    ("first_name", "James"),
                    ("company__name", "XYZ"),
                ],
            ),
            ("age", 42, [("age", 42)]),
            ("token", "abc=123", [("token", "abc=123")]),
        ]

        for arg, value, expected in test_cases:
            with self.subTest(arg=arg, value=value):
                self.assertEqual(manager.strip_args(arg, value), expected)