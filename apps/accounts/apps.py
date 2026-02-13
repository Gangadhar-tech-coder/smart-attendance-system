from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    label = 'accounts'  # This sets the app label to 'accounts' instead of 'apps_accounts'
    verbose_name = 'User Accounts'

    def ready(self):
        """Import signals when app is ready"""
        import apps.accounts.signals  # Import the signals module