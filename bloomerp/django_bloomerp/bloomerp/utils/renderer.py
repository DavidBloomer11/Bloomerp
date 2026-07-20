from typing import Any, Optional

from django.forms.widgets import Widget


def render_field(
    widget:Widget, 
    label:str, 
    name:str,
    value:Any,
    attrs:Optional[dict] = None,
    help_text:Optional[str]=None,
    required:bool=False,
    ) -> str:
    return f"<label>{label}</label>" + widget.render(
        name=name,
        value=value,
        attrs=attrs
    )