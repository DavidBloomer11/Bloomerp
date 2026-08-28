from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def _format_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, list):
        return "[" + ", ".join(_format_value(item) for item in value) + "]"
    raise TypeError(f"Unsupported TOML value: {type(value).__name__}")


def _render_table(data: dict[str, Any], prefix: tuple[str, ...] = ()) -> list[str]:
    def is_array_table(value: Any) -> bool:
        return isinstance(value, list) and bool(value) and all(
            isinstance(item, dict) for item in value
        )

    lines = [
        f"{key} = {_format_value(value)}"
        for key, value in data.items()
        if not isinstance(value, dict) and not is_array_table(value)
    ]

    for key, value in data.items():
        if not isinstance(value, dict):
            continue
        if lines:
            lines.append("")
        section = ".".join((*prefix, key))
        lines.append(f"[{section}]")
        lines.extend(_render_table(value, (*prefix, key)))

    for key, value in data.items():
        if not is_array_table(value):
            continue
        section = ".".join((*prefix, key))
        for item in value:
            if lines:
                lines.append("")
            lines.append(f"[[{section}]]")
            lines.extend(_render_table(item, (*prefix, key)))

    return lines


def write_toml_model(
    path: Path,
    model: BaseModel,
    *,
    exclude_defaults: bool = False,
) -> None:
    data = model.model_dump(
        mode="json",
        exclude_none=True,
        exclude_defaults=exclude_defaults,
    )
    rendered = "\n".join(_render_table(data))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{rendered}\n" if rendered else "", encoding="utf-8")
