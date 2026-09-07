from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile

from bloomerp.models.files.file import File
from bloomerp.tests.base import (
    BloomerpComponentTestCase,
    ExpectedResult,
    RequestSetup,
)


class TestUploadFilesComponent(BloomerpComponentTestCase):
    """Tests function `upload_files` from `bloomerp/components/files/items/upload.py`."""

    create_foreign_models = True
    view_name = "components_files_upload"

    def get_request_setups(self) -> list[RequestSetup]:
        customer = self.CustomerModel.objects.first()
        content_type = ContentType.objects.get_for_model(customer)
        return [
            RequestSetup(
                name="upload file",
                method="POST",
                user=self.admin_user,
                data={
                    "files": SimpleUploadedFile("test_file.txt", b"Test content")
                },
                expected=ExpectedResult(
                    response_validators=self._file_exists(name="test_file.txt")
                ),
            ),
            RequestSetup(
                name="upload file for object",
                method="POST",
                user=self.admin_user,
                data={
                    "content_type_id": content_type.id,
                    "object_id": customer.pk,
                    "files": SimpleUploadedFile(
                        "scoped_file.txt",
                        b"Test content",
                    ),
                },
                expected=ExpectedResult(
                    response_validators=self._file_exists(
                        name="scoped_file.txt",
                        content_type=content_type,
                        object_id=customer.pk,
                    )
                ),
            ),
        ]

    def _file_exists(self, **filters):
        return self._named_validator(
            f"file_exists({filters!r})",
            lambda _response: File.objects.filter(**filters).exists(),
        )
