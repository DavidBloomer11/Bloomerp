from django.db import models
from django.contrib.contenttypes.models import ContentType
from bloomerp.model_fields.file_field import BloomerpFileField
from bloomerp.models.base_bloomerp_model import BloomerpModel
from django.utils.translation import gettext_lazy as _
from bloomerp.models.files.file_folder import FileFolder
from django.contrib.auth import get_user_model
from django.conf import settings


# ---------------------------------
# Document Template Model
# ---------------------------------
class DocumentTemplateHeader(BloomerpModel):
    avatar = None

    class Meta(BloomerpModel.Meta):
        verbose_name = _("Document Template Header")
        verbose_name_plural = _("Document Template Headers")
        managed = True
        db_table = 'bloomerp_document_template_header'
    
    name = models.CharField(
        max_length=100,
        blank=False,
        null=False, 
        help_text=_("Name of the template header."),
        verbose_name=_("Name")) #Name of the document template header
    header = models.ImageField(
        help_text=_("Image of the header."),
        upload_to='document_templates/headers',
        verbose_name=_("Header"),
    )
    margin_top = models.FloatField(default=0.5, help_text=_("Top margin of the header in inches."), verbose_name=_("Margin Top"))
    margin_bottom = models.FloatField(default=0.0, help_text=_("Bottom margin of the header in inches."), verbose_name=_("Margin Bottom"))
    margin_left = models.FloatField(default=1.0, help_text=_("Left margin of the header in inches."), verbose_name=_("Margin Left"))
    margin_right = models.FloatField(default=1.0, help_text=_("Right margin of the header in inches."), verbose_name=_("Margin Right"))

    height = models.FloatField(default=1.0, help_text=_("Height of the header in inches."), verbose_name=_("Height"))
    
    def __str__(self):
        return self.name
