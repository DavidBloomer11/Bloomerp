import mimetypes
from pathlib import Path
from urllib.parse import urlencode, urlsplit

import bleach
import mistune
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import FileResponse, Http404, HttpResponse
from django.template import Context, Template
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from bloomerp.views.base import BaseBloomerpView


MARKDOWN_TAGS = [
    "a",
    "blockquote",
    "br",
    "code",
    "del",
    "div",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "img",
    "li",
    "ol",
    "p",
    "pre",
    "button",
    "strong",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "ul",
]
MARKDOWN_ATTRIBUTES = {
    "*": ["class"],
    "a": ["href", "title"],
    "button": [
        "aria-label",
        "data-copied-label",
        "data-copy-code",
        "data-copy-label",
        "type",
    ],
    "div": ["bloomerp-component"],
    "h1": ["id"],
    "h2": ["id"],
    "h3": ["id"],
    "h4": ["id"],
    "h5": ["id"],
    "h6": ["id"],
    "img": ["alt", "src", "title"],
}
MARKDOWN_PROTOCOLS = ["http", "https", "mailto"]
MARKDOWN_CLASSES = {
    "h1": [
        "mb-4",
        "text-3xl",
        "font-semibold",
        "tracking-tight",
        "text-primary-900",
    ],
    "h2": [
        "mb-3",
        "mt-8",
        "text-2xl",
        "font-semibold",
        "tracking-tight",
        "text-primary-900",
    ],
    "h3": ["mb-2", "mt-6", "text-xl", "font-semibold", "text-primary-900"],
    "h4": ["mb-2", "mt-5", "text-lg", "font-semibold", "text-primary-900"],
    "h5": ["mb-2", "mt-4", "text-base", "font-semibold", "text-primary-900"],
    "h6": [
        "mb-2",
        "mt-4",
        "text-sm",
        "font-semibold",
        "uppercase",
        "tracking-wide",
        "text-primary-900",
    ],
    "p": ["my-3", "leading-7", "text-dark"],
    "ul": ["my-3", "list-disc", "space-y-1", "pl-6"],
    "ol": ["my-3", "list-decimal", "space-y-1", "pl-6"],
    "li": ["leading-7", "text-dark"],
    "a": ["text-primary-600", "underline", "underline-offset-2"],
    "blockquote": [
        "my-4",
        "border-l-4",
        "border-primary-200",
        "pl-4",
        "italic",
        "text-gray-600",
    ],
    "pre": [
        "overflow-x-auto",
        "rounded-xl",
        "bg-zinc-900",
        "p-4",
        "text-sm",
        "text-zinc-100",
        "shadow-xs",
    ],
    "code": [
        "rounded",
        "bg-base",
        "px-1.5",
        "py-0.5",
        "font-mono",
        "text-sm",
        "text-primary-900",
    ],
    "img": ["my-5", "max-w-full", "rounded-xl", "border", "border-gray-200"],
    "table": ["my-5", "w-full", "border-collapse", "text-left", "text-sm"],
    "thead": ["bg-base"],
    "th": ["border", "border-gray-200", "p-2", "font-semibold", "text-primary-900"],
    "td": ["border", "border-gray-200", "p-2", "text-dark"],
    "hr": ["my-8", "border-gray-200"],
}


class MarkdownView(BaseBloomerpView, TemplateView):
    """Render a Markdown file inside the standard Bloomerp view lifecycle."""

    markdown_file: str | Path | None = None
    template_name = "views/generic/markdown.html"
    media_query_parameter = "_markdown_media"

    def get_markdown_path(self) -> Path:
        """Return the configured Markdown path relative to Bloomerp's templates directory."""
        if self.markdown_file is None:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} requires a markdown_file."
            )

        markdown_path = Path(self.markdown_file).expanduser()
        if not markdown_path.is_absolute():
            markdown_path = (
                Path(settings.BASE_DIR) / "bloomerp" / "templates" / markdown_path
            )
        markdown_path = markdown_path.resolve()

        if not markdown_path.is_file():
            raise Http404("Markdown file not found.")
        return markdown_path

    def get(self, request, *args, **kwargs) -> HttpResponse:
        """Render the document or serve an image referenced by the document."""
        media_path = request.GET.get(self.media_query_parameter)
        if media_path is not None:
            return self.serve_markdown_media(media_path)
        return super().get(request, *args, **kwargs)

    def serve_markdown_media(self, media_path: str) -> FileResponse:
        """Serve an image only when it resolves inside the Markdown directory."""
        markdown_directory = self.get_markdown_path().parent
        requested_path = Path(media_path)
        if requested_path.is_absolute():
            raise Http404("Markdown image not found.")

        image_path = (markdown_directory / requested_path).resolve()
        try:
            image_path.relative_to(markdown_directory)
        except ValueError as error:
            raise Http404("Markdown image not found.") from error

        content_type, _ = mimetypes.guess_type(image_path.name)
        if not image_path.is_file() or not content_type or not content_type.startswith("image/"):
            raise Http404("Markdown image not found.")

        return FileResponse(image_path.open("rb"), content_type=content_type)

    def get_context_data(self, **kwargs) -> dict:
        """Add rendered Markdown and its header-based table of contents."""
        context = super().get_context_data(**kwargs)
        markdown_source = self.render_markdown_template(
            self.get_markdown_path().read_text(encoding="utf-8"),
            context,
            **kwargs,
        )
        rendered_markdown, table_of_contents = self.render_markdown(markdown_source)
        context.update(
            {
                "rendered_markdown": mark_safe(rendered_markdown),
                "table_of_contents": table_of_contents,
            }
        )
        return context

    def get_markdown_context(self, **kwargs) -> dict[str, object]:
        """Return variables available while rendering the Markdown template."""
        return {}

    def render_markdown_template(
        self,
        markdown_source: str,
        context: dict[str, object] | None = None,
        **kwargs,
    ) -> str:
        """Render Django variables before converting the source to Markdown HTML."""
        template_context = dict(context or {})
        template_context.update(self.get_markdown_context(**kwargs))
        return Template(markdown_source).render(Context(template_context))

    def render_markdown(self, markdown_source: str) -> tuple[str, list[dict[str, object]]]:
        """Render safe HTML, route local images, and collect unique heading anchors."""
        renderer = mistune.create_markdown(
            escape=True,
            plugins=["strikethrough", "table", "url"],
        )
        soup = BeautifulSoup(renderer(markdown_source), "html.parser")
        table_of_contents: list[dict[str, object]] = []
        used_anchors: set[str] = set()

        for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            heading_text = heading.get_text(" ", strip=True)
            base_anchor = slugify(heading_text) or "section"
            anchor = base_anchor
            suffix = 2
            while anchor in used_anchors:
                anchor = f"{base_anchor}-{suffix}"
                suffix += 1
            used_anchors.add(anchor)
            heading["id"] = anchor
            level = int(heading.name[1])
            table_of_contents.append(
                {
                    "anchor": anchor,
                    "level": level,
                    "indent_rem": max(level - 1, 0) * 0.75,
                    "title": heading_text,
                }
            )

        for image in soup.find_all("img", src=True):
            source = str(image["src"])
            parsed_source = urlsplit(source)
            if (
                parsed_source.scheme
                or parsed_source.netloc
                or source.startswith(("/", "#"))
            ):
                continue
            image["src"] = (
                f"{self.request.path}?"
                f"{urlencode({self.media_query_parameter: parsed_source.path})}"
            )

        self.apply_markdown_classes(soup)
        self.add_code_copy_buttons(soup)

        cleaned_html = bleach.clean(
            str(soup),
            tags=MARKDOWN_TAGS,
            attributes=MARKDOWN_ATTRIBUTES,
            protocols=MARKDOWN_PROTOCOLS,
            strip=True,
        )
        return cleaned_html, table_of_contents

    def apply_markdown_classes(self, soup: BeautifulSoup) -> None:
        """Apply Bloomerp's Tailwind styling to rendered Markdown elements."""
        for tag_name, classes in MARKDOWN_CLASSES.items():
            for element in soup.find_all(tag_name):
                element["class"] = [*element.get("class", []), *classes]

                if tag_name == "code" and element.parent and element.parent.name == "pre":
                    element["class"] = [
                        "block",
                        "bg-transparent",
                        "p-0",
                        "font-mono",
                        "text-inherit",
                    ]

    def add_code_copy_buttons(self, soup: BeautifulSoup) -> None:
        """Wrap fenced code blocks with an HTMX-safe clipboard component."""
        for code_block in list(soup.find_all("pre")):
            wrapper = soup.new_tag(
                "div",
                attrs={
                    "bloomerp-component": "markdown-code-block",
                    "class": ["markdown-code-block"],
                },
            )
            code_block.wrap(wrapper)

            copy_label = str(_("Copy"))
            copied_label = str(_("Copied"))
            button = soup.new_tag(
                "button",
                attrs={
                    "aria-label": copy_label,
                    "class": ["markdown-code-copy"],
                    "data-copied-label": copied_label,
                    "data-copy-code": "",
                    "data-copy-label": copy_label,
                    "type": "button",
                },
            )
            button.string = copy_label
            wrapper.insert(0, button)
