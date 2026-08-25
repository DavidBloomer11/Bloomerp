from django.db import models
from bloomerp.models.base_bloomerp_model import BloomerpModel, FieldLayout, LayoutItem, LayoutRow
from bloomerp.models.definition import BloomerpModelConfig, DetailViewSettings
from django.utils.translation import gettext_lazy as _, gettext_noop

class TodoLabel(BloomerpModel):
    """
    Model representing a label that can be assigned to to-do items.
    """
    bloomerp_config = BloomerpModelConfig(
        detail_view_settings=DetailViewSettings(
            layout=[FieldLayout(
                rows=[
                    LayoutRow(
                        title=gettext_noop("Label Details"),
                        columns=2,
                        items=[
                            LayoutItem(id="name", colspan=1),
                            LayoutItem(id="color", colspan=1),
                        ],
                    )
                ]
            )],
        )
    )

    class Meta:
        verbose_name = _("Todo Label")
        verbose_name_plural = _("Todo Labels")
        managed = True
        db_table = 'bloomerp_todo_label'

    avatar = None
    name = models.CharField(
        max_length=100,
        verbose_name=_("Name"),
    )
    color = models.CharField(
        max_length=7,
        verbose_name=_("Color"), 
    )  

    def __str__(self):
        return self.name
