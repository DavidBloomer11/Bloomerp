import re

from django import forms


DEFAULT_ICON_CHOICES = [
    {"value": "fa-solid fa-folder", "label": "Folder"},
    {"value": "fa-solid fa-link", "label": "Link"},
    {"value": "fa-solid fa-dollar-sign", "label": "Dollar"},
    {"value": "fa-solid fa-book", "label": "Book"},
    {"value": "fa-solid fa-graduation-cap", "label": "Graduation"},
    {"value": "fa-solid fa-pen", "label": "Pen"},
    {"value": "fa-solid fa-tag", "label": "Tag"},
    {"value": "fa-solid fa-code", "label": "Code"},
    {"value": "fa-solid fa-terminal", "label": "Terminal"},
    {"value": "fa-solid fa-music", "label": "Music"},
    {"value": "fa-solid fa-cake-candles", "label": "Cake"},
    {"value": "fa-solid fa-scissors", "label": "Scissors"},
    {"value": "fa-solid fa-palette", "label": "Palette"},
    {"value": "fa-solid fa-stethoscope", "label": "Stethoscope"},
    {"value": "fa-solid fa-gear", "label": "Settings"},
    {"value": "fa-solid fa-leaf", "label": "Leaf"},
    {"value": "fa-solid fa-briefcase", "label": "Briefcase"},
    {"value": "fa-solid fa-chart-bar", "label": "Chart"},
    {"value": "fa-solid fa-user", "label": "User"},
    {"value": "fa-solid fa-dumbbell", "label": "Fitness"},
    {"value": "fa-solid fa-book-open", "label": "Open Book"},
    {"value": "fa-solid fa-scale-balanced", "label": "Scale"},
    {"value": "fa-solid fa-globe", "label": "Globe"},
    {"value": "fa-solid fa-paw", "label": "Paw"},
    {"value": "fa-solid fa-flask", "label": "Flask"},
    {"value": "fa-solid fa-brain", "label": "Brain"},
    {"value": "fa-solid fa-heart", "label": "Heart"},
    {"value": "fa-solid fa-gift", "label": "Gift"},
    {"value": "fa-solid fa-bolt", "label": "Bolt"},
    {"value": "fa-solid fa-star", "label": "Star"},
    {"value": "fa-solid fa-camera", "label": "Camera"},
    {"value": "fa-solid fa-comment", "label": "Comment"},
    {"value": "fa-solid fa-cloud", "label": "Cloud"},
    {"value": "fa-solid fa-calendar", "label": "Calendar"},
    {"value": "fa-solid fa-check", "label": "Check"},
    {"value": "fa-solid fa-fire", "label": "Fire"},
    {"value": "fa-solid fa-house", "label": "House"},
    {"value": "fa-solid fa-building", "label": "Building"},
    {"value": "fa-solid fa-city", "label": "City"},
    {"value": "fa-solid fa-store", "label": "Store"},
    {"value": "fa-solid fa-warehouse", "label": "Warehouse"},
    {"value": "fa-solid fa-truck", "label": "Truck"},
    {"value": "fa-solid fa-car", "label": "Car"},
    {"value": "fa-solid fa-train", "label": "Train"},
    {"value": "fa-solid fa-plane", "label": "Plane"},
    {"value": "fa-solid fa-ship", "label": "Ship"},
    {"value": "fa-solid fa-map", "label": "Map"},
    {"value": "fa-solid fa-location-dot", "label": "Location"},
    {"value": "fa-solid fa-route", "label": "Route"},
    {"value": "fa-solid fa-compass", "label": "Compass"},
    {"value": "fa-solid fa-clock", "label": "Clock"},
    {"value": "fa-solid fa-hourglass-half", "label": "Hourglass"},
    {"value": "fa-solid fa-envelope", "label": "Envelope"},
    {"value": "fa-solid fa-phone", "label": "Phone"},
    {"value": "fa-solid fa-video", "label": "Video"},
    {"value": "fa-solid fa-microphone", "label": "Microphone"},
    {"value": "fa-solid fa-headset", "label": "Headset"},
    {"value": "fa-solid fa-file", "label": "File"},
    {"value": "fa-solid fa-file-lines", "label": "Document"},
    {"value": "fa-solid fa-file-invoice", "label": "Invoice"},
    {"value": "fa-solid fa-receipt", "label": "Receipt"},
    {"value": "fa-solid fa-clipboard-list", "label": "Clipboard List"},
    {"value": "fa-solid fa-list-check", "label": "Checklist"},
    {"value": "fa-solid fa-table", "label": "Table"},
    {"value": "fa-solid fa-chart-line", "label": "Line Chart"},
    {"value": "fa-solid fa-chart-pie", "label": "Pie Chart"},
    {"value": "fa-solid fa-magnifying-glass", "label": "Search"},
    {"value": "fa-solid fa-wrench", "label": "Wrench"},
    {"value": "fa-solid fa-screwdriver-wrench", "label": "Tools"},
    {"value": "fa-solid fa-hammer", "label": "Hammer"},
    {"value": "fa-solid fa-key", "label": "Key"},
    {"value": "fa-solid fa-lock", "label": "Lock"},
    {"value": "fa-solid fa-shield-halved", "label": "Shield"},
    {"value": "fa-solid fa-database", "label": "Database"},
    {"value": "fa-solid fa-server", "label": "Server"},
    {"value": "fa-solid fa-laptop-code", "label": "Laptop Code"},
    {"value": "fa-solid fa-mobile-screen-button", "label": "Mobile"},
    {"value": "fa-solid fa-wifi", "label": "Wifi"},
    {"value": "fa-solid fa-plug", "label": "Plug"},
    {"value": "fa-solid fa-lightbulb", "label": "Lightbulb"},
    {"value": "fa-solid fa-trophy", "label": "Trophy"},
    {"value": "fa-solid fa-medal", "label": "Medal"},
    {"value": "fa-solid fa-award", "label": "Award"},
    {"value": "fa-solid fa-rocket", "label": "Rocket"},
    {"value": "fa-solid fa-seedling", "label": "Seedling"},
    {"value": "fa-solid fa-hand-holding-heart", "label": "Care"},
]

ICON_COLOR_CHOICES = [
    {"value": "#000000", "label": "Black"},
    {"value": "#FF4D4F", "label": "Red"},
    {"value": "#FF6A21", "label": "Orange"},
    {"value": "#F4B400", "label": "Yellow"},
    {"value": "#12C152", "label": "Green"},
    {"value": "#2383EB", "label": "Blue"},
    {"value": "#4F46E5", "label": "Indigo"},
    {"value": "#8B5CF6", "label": "Violet"},
    {"value": "#F35BA5", "label": "Pink"},
    {"value": "#14B8A6", "label": "Teal"},
    {"value": "#A855F7", "label": "Purple"},
    {"value": "#64748B", "label": "Slate"},
]

TEXT_COLOR_RE = re.compile(r"text-\[(#[0-9A-Fa-f]{6})\]")
BG_COLOR_RE = re.compile(r"bg-\[(#[0-9A-Fa-f]{6})\]/(?:4|6)")


def normalize_color_value(value: str | None) -> str:
    normalized = str(value or "").strip().upper()
    if not normalized:
        return ""
    if not normalized.startswith("#"):
        normalized = f"#{normalized}"
    return normalized


def build_color_bg_class(color: str) -> str:
    return f"bg-[{color}]/6"


def build_color_text_class(color: str) -> str:
    return f"text-[{color}]"


def build_icon_value(icon_value: str, color: str | None = None) -> str:
    normalized_icon = str(icon_value or "").strip()
    normalized_color = normalize_color_value(color)

    if not normalized_icon:
        return ""

    if not normalized_color:
        return normalized_icon

    return f"{normalized_icon} {build_color_bg_class(normalized_color)} {build_color_text_class(normalized_color)}"


def parse_icon_value(value: str | None) -> dict[str, str]:
    normalized_value = str(value or "").strip()
    if not normalized_value:
        return {
            "icon": "",
            "color": "",
            "bg_class": "",
            "text_class": "",
        }

    text_match = TEXT_COLOR_RE.search(normalized_value)
    bg_match = BG_COLOR_RE.search(normalized_value)
    color = normalize_color_value((text_match or bg_match).group(1) if (text_match or bg_match) else "")
    icon = BG_COLOR_RE.sub("", normalized_value)
    icon = TEXT_COLOR_RE.sub("", icon)
    icon = " ".join(icon.split())

    return {
        "icon": icon,
        "color": color,
        "bg_class": build_color_bg_class(color) if color else "",
        "text_class": build_color_text_class(color) if color else "",
    }


def get_icon_color_choices():
    return [
        {
            **color,
            "bg_class": build_color_bg_class(color["value"]),
            "text_class": build_color_text_class(color["value"]),
        }
        for color in ICON_COLOR_CHOICES
    ]


def normalize_icon_choices(icons):
    if icons is None:
        return list(DEFAULT_ICON_CHOICES)

    normalized = []
    for icon in icons:
        if isinstance(icon, dict):
            value = str(icon.get("value", "")).strip()
            label = str(icon.get("label", value)).strip()
        elif isinstance(icon, (list, tuple)) and len(icon) >= 1:
            value = str(icon[0]).strip()
            label = str(icon[1]).strip() if len(icon) > 1 else value
        else:
            value = str(icon).strip()
            label = value

        if not value:
            continue

        normalized.append({"value": value, "label": label})

    return normalized


def get_icon_values(icons):
    return [icon["value"] for icon in normalize_icon_choices(icons)]


class IconPickerWidget(forms.Widget):
    template_name = "widgets/icon_picker_widget.html"

    def __init__(self, attrs=None, icons=None):
        attrs = attrs or {}
        existing_class = attrs.get("class", "").strip()
        if "input" not in existing_class:
            attrs["class"] = f"input w-full {existing_class}".strip()
        super().__init__(attrs)
        self.icons = normalize_icon_choices(icons)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        icon_lookup = {icon["value"]: icon["label"] for icon in self.icons}
        parsed_value = parse_icon_value(context["widget"].get("value") or "")
        selected_icon = parsed_value["icon"]
        selected_label = icon_lookup.get(selected_icon, selected_icon)

        invalid = False
        if (attrs or {}).get("aria-invalid", "false") == "true":
            invalid = True

        context["widget"].update(
            {
                "icons": self.icons,
                "colors": get_icon_color_choices(),
                "selected_label": selected_label,
                "selected_icon": selected_icon,
                "selected_color": parsed_value["color"],
                "selected_color_bg_class": parsed_value["bg_class"],
                "selected_color_text_class": parsed_value["text_class"],
                "default_color": ICON_COLOR_CHOICES[0]["value"],
                "invalid": invalid,
            }
        )
        return context
