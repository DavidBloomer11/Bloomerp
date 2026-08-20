from django.apps import AppConfig

from bloomerp.config.definition import BloomerpAppI18nSettings


class __APP_CLASS_NAME__(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "__APP_NAME__"
    # Change this when model and route labels are authored in another language.
    bloomerp_i18n = BloomerpAppI18nSettings(source_language="en")
