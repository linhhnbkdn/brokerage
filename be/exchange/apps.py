from django.apps import AppConfig


class ExchangeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "exchange"
    
    def ready(self) -> None:
        """Initialize app when Django starts"""
        # Import signal handlers or startup tasks here if needed
        pass
