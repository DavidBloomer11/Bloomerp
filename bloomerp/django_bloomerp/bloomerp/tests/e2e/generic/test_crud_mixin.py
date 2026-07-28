from playwright.sync_api import Locator

class TestCrudE2EMixin:
    def locate_field(self, field_id) -> Locator:
        """
        Locate a field by its id
        """
        return self.page.locator("#id_"+field_id)