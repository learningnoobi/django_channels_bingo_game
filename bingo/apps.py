from django.apps import AppConfig


class BingoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bingo'

    def ready(self):
        import bingo.signals
