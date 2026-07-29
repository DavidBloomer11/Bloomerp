from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from django import forms
from django.core.files.uploadedfile import UploadedFile
from django.db.models import Model

from bloomerp.form_fields.structured_value import StructuredFormValue


@dataclass
class FilesCleanedData(StructuredFormValue):
    files: list[UploadedFile] = field(default_factory=list)
    _saved: bool = field(default=False, init=False, repr=False)

    def save(self, parent: Model, *, user=None) -> None:
        from bloomerp.models.files.file import File
        if self._saved or not self.files:
            return

        File.upload_files_to_object(
            parent,
            self.files
        )
        self._saved = True

    def serialize(self) -> list[str]:
        return [getattr(uploaded_file, "name", str(uploaded_file)) for uploaded_file in self.files]


class FilesRelationField(forms.Field):
    """Return uploaded object files as a structured, persistable value."""

    def bound_data(self, data: Any, initial: Any) -> Any:
        if data in (None, "", [], ()):
            return initial
        return data

    def clean(self, value: Any) -> FilesCleanedData:
        value = super().clean(value) or []
        if not isinstance(value, (list, tuple)):
            value = [value]
        return FilesCleanedData(
            files=[item for item in value if isinstance(item, UploadedFile)],
        )
