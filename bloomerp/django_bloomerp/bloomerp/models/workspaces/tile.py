from bloomerp.model_fields.icon_field import IconField
from bloomerp.models.base_bloomerp_model import BloomerpModel
from django.db import models
from django.utils.translation import gettext_lazy as _


def get_tile_type_choices():
    from bloomerp.workspaces.tiles import TileType

    return [(tile.name, tile.value.name) for tile in TileType]

class Tile(BloomerpModel):
    """
    A widget represents a visual item that can be placed on a workspace.
    """
    class Meta(BloomerpModel.Meta):
        verbose_name = _("Tile")
        verbose_name_plural = _("Tiles")
        managed = True
        db_table = 'bloomerp_tile'

    name = models.CharField(
        max_length=255, 
        help_text=_("Name of the widget"),
        verbose_name=_("Name"),
        )
    description = models.TextField(
        blank=True,
        null=True,
        help_text=_("Description of the widget"),
        verbose_name=_("Description"),
        )
    type = models.CharField(
        help_text=_("The type of tile"),
        max_length=32,
        choices=get_tile_type_choices,
        verbose_name=_("Type"),
    )
    icon = IconField(
        default="fa fa-chart-simple",
        verbose_name=_("Icon"),
    )
    schema = models.JSONField(verbose_name=_("Schema"))
    auto_generated = models.BooleanField(
        default=False,
        verbose_name=_("Auto Generated"),
    )


    def __str__(self):
        return self.name
    
    
