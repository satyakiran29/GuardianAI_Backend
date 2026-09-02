from django.apps import AppConfig

class GuardianApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'guardian_api'

    def ready(self):
        try:
            from .keep_alive import start_keep_alive
            start_keep_alive()
        except Exception as e:
            pass
