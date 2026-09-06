from django.apps import AppConfig

from bloomerp.config.definition import BloomerpAppI18nSettings


class BloomerpModulesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bloomerp_modules'
    bloomerp_i18n = BloomerpAppI18nSettings(source_language="en")

    def ready(self):
        from . import views