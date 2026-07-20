from django import forms
from django.test import SimpleTestCase

from bloomerp.models.base_bloomerp_model import FieldLayout, LayoutItem, LayoutRow
from bloomerp.views.mixins.layout_form_mixin import LayoutFormMixin
from bloomerp.views.mixins.layout_mixin import LayoutMixin


class TestLayoutFormMixin2(SimpleTestCase):
    def test_transformed_layout_applies_item_presentation_without_extractors(self):
        source_layout = FieldLayout(
            rows=[LayoutRow(columns=1, items=[LayoutItem(id="summary")])]
        )

        class TestView(LayoutMixin):
            item_has_border = True
            ts_item_component = "summary-item"

            def get_layout(self):
                return source_layout

        transformed_item = TestView().get_transformed_layout().rows[0].items[0]

        self.assertTrue(transformed_item.border)
        self.assertEqual(transformed_item.component_name, "summary-item")
        self.assertFalse(source_layout.rows[0].items[0].border)

    def test_transformed_layout_maps_bound_form_fields_without_mutating_source(self):
        source_layout = FieldLayout(
            rows=[
                LayoutRow(
                    columns=2,
                    items=[LayoutItem(id="first_name")],
                )
            ]
        )

        class TestForm(forms.Form):
            first_name = forms.CharField(initial="Ada")

        class TestView(LayoutFormMixin):
            def get_layout(self):
                return source_layout

            def get_form(self):
                return TestForm()

        transformed_layout = TestView().get_transformed_layout()
        transformed_item = transformed_layout.rows[0].items[0]

        self.assertIn('name="first_name"', transformed_item.content)
        self.assertIn("Ada", transformed_item.content)
        self.assertIsNone(source_layout.rows[0].items[0].content)

    def test_transformed_layout_respects_form_field_disabled_state(self):
        source_layout = FieldLayout(
            rows=[LayoutRow(columns=1, items=[LayoutItem(id="computed_value")])]
        )

        class TestForm(forms.Form):
            computed_value = forms.CharField(initial="Read only", disabled=True)

        class TestView(LayoutFormMixin):
            def get_layout(self):
                return source_layout

            def get_form(self):
                return TestForm()

        transformed_item = TestView().get_transformed_layout().rows[0].items[0]

        self.assertIn("disabled", transformed_item.content)

    def test_transformed_layout_retains_invisible_items_with_labels_without_rendering_fields(self):
        source_layout = FieldLayout(
            rows=[LayoutRow(columns=1, items=[LayoutItem(id="private_field")])]
        )

        class TestForm(forms.Form):
            private_field = forms.CharField(label="Private field")

        class TestView(LayoutFormMixin):
            is_visible_extractor_func = lambda self, item: False

            def get_layout(self):
                return source_layout

            def get_form(self):
                return TestForm()

        transformed_item = TestView().get_transformed_layout().rows[0].items[0]

        self.assertEqual(transformed_item.id, "private_field")
        self.assertFalse(transformed_item.is_visible)
        self.assertEqual(transformed_item.label, "Private field")
        self.assertIsNone(transformed_item.content)
        self.assertTrue(source_layout.rows[0].items[0].is_visible)
        self.assertIsNone(source_layout.rows[0].items[0].label)
