from django.apps import AppConfig


class InvoiceAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'invoice_app'
    verbose_name = 'Application de Facturation'
    
    def ready(self):
        """Register signal handlers when app is ready"""
        import invoice_app.signals
