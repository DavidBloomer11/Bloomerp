from bloomerp.tests.base import BaseBloomerpModelTestCase
from bloomerp.widgets.one_to_many_field_widget import OneToManyFieldWidget
from django.http import QueryDict

class TestCreateView(BaseBloomerpModelTestCase):
    create_foreign_models = True
    
    # --------------------------------------
    # TESTS
    # --------------------------------------
    def test_widget_skips_some_fields(self):
        """
        UC: We don't want particular fields to be rendered for the one-to-many widget
        Expected result: some fields are skipped
        """
        
        # 0. Set the skipped fields
        SKIPPED_FIELDS = ["created_by", "updated_by", "datetime_created", "datetime_updated"]
        
        # 1. Create the widget using the related model and parent model
        widget = OneToManyFieldWidget(attrs={
            "related_model" : self.CountryModel,
            "parent_model" : self.PlanetModel,
        })
        
        # 2. Render the widget to get the columns
        widget_html = widget.render(name="test_widget", value=None, attrs={})
        
        # 3. Check that the skipped fields are not present in the widget HTML
        for field_name in SKIPPED_FIELDS:
            self.assertNotIn(field_name, widget_html)
            
    def test_widget_renders_fields_given_as_config(self):
        """
        UC: We want widgets with a specific layout config to render the necessary fields
        Expected result: the fields specified in the config are rendered
        """
        
        # 0. Set the fields to be rendered
        RENDERED_FIELDS = ["first_name", "last_name"]
        
        # 1. Create the widget using the related model and parent model, and specify the fields to render
        widget = OneToManyFieldWidget(attrs={
            "related_model" : self.CustomerModel,
            "parent_model" : self.CountryModel,
            "layout_config" : {
                "inline_fields" : RENDERED_FIELDS
            }
        })
        
        # 2. Render the widget to get the columns
        widget_html = widget.render(name="test_widget", value=None, attrs={})
        
        # 3. Check that the specified fields are present in the widget HTML
        for field_name in RENDERED_FIELDS:
            self.assertIn(field_name, widget_html)
            
        self.assertNotIn("age", widget_html)  # Ensure that a field not specified is not rendered

    def test_widget_collects_nested_rows_for_form_cleaning(self):
        widget = OneToManyFieldWidget()
        data = QueryDict(mutable=True)
        data.update(
            {
                "contracts__1__id": "20",
                "contracts__1__status": "draft",
                "contracts__0__id": "10",
                "contracts__0__status": "active",
                "contracts__0__DELETE": "1",
                "unrelated": "ignored",
            }
        )

        self.assertEqual(
            widget.value_from_datadict(data, {}, "contracts"),
            [
                {"id": "10", "status": "active", "DELETE": "1"},
                {"id": "20", "status": "draft"},
            ],
        )
        
    
