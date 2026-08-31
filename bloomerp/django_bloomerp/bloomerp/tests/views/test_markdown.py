from bs4 import BeautifulSoup
from django.test import TestCase, override_settings
from django.urls import path, reverse

from bloomerp.models import User
from bloomerp.views.base import BaseBloomerpView
from bloomerp.views.generic.markdown import MarkdownView


class MarkdownFixtureView(MarkdownView):
    markdown_file = "tests/markdown/simple.md"

    def get_markdown_context(self, **kwargs) -> dict[str, object]:
        return {"document_title": "Markdown view"}


urlpatterns = [
    path("markdown/", MarkdownFixtureView.as_view(), name="test_markdown_view"),
]


@override_settings(ROOT_URLCONF=__name__)
class MarkdownViewTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="markdown-view-user",
            password="testpass123",
            is_staff=True,
        )
        self.client.force_login(self.user)
        self.url = reverse("test_markdown_view")

    def test_view_renders_markdown_headers_toc_and_routed_images(self) -> None:
        """
        Use case: A routed Bloomerp view displays a Markdown file containing images.
        Expected result: The document, responsive table of contents, and routed image URLs render.
        """
        # 1. Request the Markdown route through the main HTMX target.
        response = self.client.get(
            self.url,
            HTTP_HX_REQUEST="true",
            HTTP_HX_TARGET="main-content",
        )

        # 2. Verify the view contract and rendered Markdown structure.
        self.assertEqual(response.status_code, 200)
        self.assertTrue(issubclass(MarkdownFixtureView, BaseBloomerpView))
        soup = BeautifulSoup(response.content, "html.parser")
        self.assertEqual(soup.find("h1")["id"], "markdown-view")
        self.assertIn("text-primary-900", soup.find("h1").get("class", []))
        self.assertContains(response, "This remains visible as text: {{ literal_variable }}")
        self.assertIsNotNone(soup.find("a", href="#images"))
        self.assertIn("markdown-view-toc", soup.find("aside").get("class", []))
        layout = soup.find("article").parent
        self.assertIn("markdown-view-layout", layout.get("class", []))

        # 3. Verify code blocks receive explicit Bloomerp styling.
        code_block = soup.find("pre")
        self.assertIn("rounded-xl", code_block.get("class", []))
        self.assertIn("bg-zinc-900", code_block.get("class", []))
        self.assertIn("text-zinc-100", code_block.get("class", []))
        code_wrapper = code_block.parent
        self.assertEqual(
            code_wrapper.get("bloomerp-component"),
            "markdown-code-block",
        )
        copy_button = code_wrapper.find("button", attrs={"data-copy-code": ""})
        self.assertEqual(copy_button.get_text(strip=True), "Copy")

        # 4. Verify every local image is routed back through the registered view.
        images = soup.find_all("img")
        self.assertEqual(len(images), 2)
        expected_source = f"{self.url}?_markdown_media=images%2Fbloomerp-mark.svg"
        self.assertTrue(all(image["src"] == expected_source for image in images))

        # 5. Request the routed image and verify its media response.
        image_response = self.client.get(images[0]["src"])
        self.assertEqual(image_response.status_code, 200)
        self.assertEqual(image_response["Content-Type"], "image/svg+xml")
        self.assertIn(b"<svg", b"".join(image_response.streaming_content))

    def test_routed_images_cannot_escape_the_markdown_directory(self) -> None:
        """
        Use case: A media request attempts to traverse outside the Markdown directory.
        Expected result: The routed view rejects the request without exposing the file.
        """
        # 1. Request a path outside the configured Markdown directory.
        response = self.client.get(
            self.url,
            {"_markdown_media": "../../test_markdown.py"},
        )

        # 2. Verify the file is not served.
        self.assertEqual(response.status_code, 404)
