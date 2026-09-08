from types import SimpleNamespace
from unittest.mock import patch

from django.template.loader import render_to_string
from django.test import SimpleTestCase, override_settings
from django.utils import timezone

from bloomerp.templatetags.bloomerp import (
    ACTIVITY_LOG_VALUE_MAX_LENGTH,
    activity_log_html,
)


class ActivityLogHtmlFilterTests(SimpleTestCase):
    def test_activity_log_html_preserves_safe_formatting(self):
        """
        Use case: An activity-log value contains HTML produced by the text editor.
        Expected result: Supported formatting renders as HTML instead of visible markup.
        """
        # 1. Sanitize a value containing supported editor formatting.
        rendered = activity_log_html("<p><strong>Important</strong> update</p>")

        # 2. Verify the safe formatting remains in the rendered value.
        self.assertEqual(str(rendered), "<p><strong>Important</strong> update</p>")

    def test_activity_log_html_removes_executable_content(self):
        """
        Use case: An activity-log value contains scripts and executable HTML attributes.
        Expected result: The value remains readable without executable browser content.
        """
        # 1. Sanitize common script injection vectors.
        rendered = activity_log_html(
            '<p onclick="alert(1)">Update</p>'
            '<script>alert(2)</script>'
            '<a href="javascript:alert(3)">Open</a>'
        )

        # 2. Verify executable tags, attributes, and URL schemes are removed.
        self.assertIn("Update", str(rendered))
        self.assertNotIn("<script", str(rendered))
        self.assertNotIn("onclick", str(rendered))
        self.assertNotIn("javascript:", str(rendered))

    def test_activity_log_html_truncates_visible_text_and_closes_tags(self):
        """
        Use case: An activity-log value contains more text than the sidebar should display.
        Expected result: Visible text is capped and the resulting HTML remains well formed.
        """
        # 1. Sanitize a long formatted value.
        rendered = str(
            activity_log_html(
                f"<p><strong>{'a' * (ACTIVITY_LOG_VALUE_MAX_LENGTH + 50)}</strong></p>"
            )
        )

        # 2. Verify truncation adds an ellipsis and preserves closing tags.
        self.assertIn("…", rendered)
        self.assertTrue(rendered.endswith("</strong></p>"))
        self.assertLessEqual(
            rendered.count("a"),
            ACTIVITY_LOG_VALUE_MAX_LENGTH,
        )

    def test_activity_log_template_uses_sanitized_html_for_changed_values(self):
        """
        Use case: The detail sidebar renders an activity entry containing editor HTML.
        Expected result: Formatting renders in both the summary and details without scripts.
        """
        # 1. Build an activity entry containing safe formatting and script injection vectors.
        value = '<strong>Visible</strong><script>alert("xss")</script>'
        entry = SimpleNamespace(
            action="CHANGE",
            actor=None,
            payload=[{"field": "notes", "from": "", "to": value}],
            source="DETAIL",
            summary_string=f"System changed the field 'notes' to {value}",
            timestamp=timezone.now(),
        )

        # 2. Render the same template used by the activity-log component.
        rendered = render_to_string(
            "views/generic/detail/activity.html",
            {"queryset": [entry]},
        )

        # 3. Verify formatting renders in both locations while scripts never reach the page.
        self.assertEqual(rendered.count("<strong>Visible</strong>"), 2)
        self.assertNotIn("<script", rendered)
        self.assertNotIn("&lt;strong&gt;", rendered)


class ViteBundleTemplateTests(SimpleTestCase):
    @override_settings(DEBUG=False)
    @patch("bloomerp.templatetags.bloomerp.version", return_value="1.15.13")
    def test_built_bundle_url_is_versioned(self, _version):
        """
        Use case: A browser loads compiled assets after a Bloomerp upgrade.
        Expected result: The package version changes the bundle URL and bypasses stale caches.
        """
        # 1. Render the production bundle snippet for a known package version.
        rendered = render_to_string("snippets/vite_bundle.html")

        # 2. Verify the compiled entry URL includes the release cache key.
        self.assertIn("/static/bloomerp/js/dist/main.js?v=1.15.13", rendered)
