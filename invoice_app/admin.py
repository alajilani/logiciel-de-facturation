from django.contrib import admin
from .models import (
    Client, Product, CompanyInfo, Invoice, InvoiceItem, Payment, Quote, QuoteItem, 
    Notification, EmailTemplate, AuditLog, AnomalyDetection, RevenueForecast, 
    IntelligentAlert, AccountingSynchronization
)

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'country', 'created_at']
    list_filter = ['country', 'created_at']
    search_fields = ['name', 'email', 'phone']
    fieldsets = (
        ('Informations générales', {'fields': ('name', 'email', 'phone', 'country')}),
        ('Adresses', {'fields': ('delivery_address', 'billing_address')}),
        ('TVA', {'fields': ('tva_intra',)}),
    )

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'reference', 'price', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'reference']
    fieldsets = (
        ('Informations', {'fields': ('name', 'reference', 'price', 'description')}),
    )

@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Informations générales', {'fields': ('name', 'address', 'phone', 'email', 'website')}),
        ('Identifiants fiscaux', {'fields': ('siret', 'siren', 'tva_number')}),
        ('Autres', {'fields': ('logo', 'country')}),
    )

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1

@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'description', 'quantity', 'price']
    list_filter = ['invoice__date']
    search_fields = ['invoice__invoice_number', 'description']

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'client', 'date', 'total', 'payment_status', 'amount_paid']
    list_filter = ['payment_status', 'date', 'client']
    search_fields = ['invoice_number', 'client__name']
    readonly_fields = ['invoice_number', 'subtotal', 'total_discount', 'tva_amount', 'total', 'created_at', 'updated_at']
    inlines = [InvoiceItemInline]
    fieldsets = (
        ('Informations de base', {'fields': ('invoice_number', 'client', 'date', 'due_date', 'payment_method')}),
        ('Détails', {'fields': ('subtotal', ('remise_percentage', 'remise_amount'), 
                                 ('rabais_percentage', 'rabais_amount'),
                                 ('escompte_percentage', 'escompte_amount'),
                                 'total_discount', 'tva_amount', 'total')}),
        ('Paiement', {'fields': ('payment_status', 'amount_paid', 'is_credit_note', 'credit_note_reason', 'original_invoice')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'amount', 'payment_date', 'payment_method']
    list_filter = ['payment_date', 'payment_method', 'invoice__client']
    search_fields = ['invoice__invoice_number', 'reference']
    readonly_fields = ['created_at']


class QuoteItemInline(admin.TabularInline):
    model = QuoteItem
    extra = 1


@admin.register(QuoteItem)
class QuoteItemAdmin(admin.ModelAdmin):
    list_display = ['quote', 'description', 'quantity', 'price']
    list_filter = ['quote__date']
    search_fields = ['quote__quote_number', 'description']


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ['quote_number', 'client', 'date', 'total', 'status', 'validity_date']
    list_filter = ['status', 'date', 'validity_date', 'client']
    search_fields = ['quote_number', 'client__name']
    readonly_fields = ['quote_number', 'subtotal', 'total_discount', 'tva_amount', 'total', 'created_at', 'updated_at']
    inlines = [QuoteItemInline]
    fieldsets = (
        ('Informations de base', {'fields': ('quote_number', 'client', 'date', 'validity_date', 'status')}),
        ('Détails', {'fields': ('subtotal', ('remise_percentage', 'remise_amount'), 
                                 ('rabais_percentage', 'rabais_amount'),
                                 ('escompte_percentage', 'escompte_amount'),
                                 'total_discount', 'tva_amount', 'total')}),
        ('Conversion', {'fields': ('converted_invoice',)}),
        ('Notes', {'fields': ('terms_conditions', 'notes')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['type', 'client', 'status', 'created_at', 'sent_at']
    list_filter = ['type', 'status', 'created_at']
    search_fields = ['client__name', 'recipient_email', 'subject']
    readonly_fields = ['created_at', 'sent_at', 'type', 'client', 'invoice', 'quote']
    fieldsets = (
        ('Informations', {'fields': ('type', 'status', 'client', 'recipient_email')}),
        ('Contenu', {'fields': ('subject', 'message')}),
        ('Références', {'fields': ('invoice', 'quote')}),
        ('Historique', {'fields': ('created_at', 'sent_at', 'error_message'), 'classes': ('collapse',)}),
    )


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['template_type', 'is_active', 'updated_at']
    list_filter = ['is_active', 'updated_at']
    fieldsets = (
        ('Template', {'fields': ('template_type', 'is_active')}),
        ('Contenu', {'fields': ('subject', 'body')}),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'action', 'model', 'object_id', 'user', 'ip_address']
    list_filter = ['action', 'model', 'timestamp', 'user']
    search_fields = ['user', 'object_str', 'ip_address']
    readonly_fields = ['action', 'model', 'object_id', 'object_str', 'user', 'ip_address', 'old_values', 'new_values', 'timestamp']
    fieldsets = (
        ('Informations', {'fields': ('action', 'model', 'object_id', 'object_str')}),
        ('Utilisateur', {'fields': ('user', 'ip_address')}),
        ('Modifications', {'fields': ('old_values', 'new_values')}),
        ('Timestamp', {'fields': ('timestamp',)}),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


# ============================================================================
# TIER 3 - BONUS MASTER: Admin classes pour IA/Intelligence
# ============================================================================

@admin.register(AnomalyDetection)
class AnomalyDetectionAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'anomaly_type', 'severity', 'confidence', 'is_resolved', 'detected_at']
    list_filter = ['anomaly_type', 'severity', 'is_resolved', 'detected_at']
    search_fields = ['invoice__invoice_number', 'description']
    readonly_fields = ['detected_at', 'detected_value', 'expected_value', 'confidence']
    fieldsets = (
        ('Anomalie', {'fields': ('invoice', 'anomaly_type', 'severity', 'description')}),
        ('Détection', {'fields': ('detected_value', 'expected_value', 'confidence')}),
        ('Résolution', {'fields': ('is_resolved', 'resolved_at', 'resolution_notes')}),
        ('Historique', {'fields': ('detected_at',), 'classes': ('collapse',)}),
    )


@admin.register(RevenueForecast)
class RevenueForecastAdmin(admin.ModelAdmin):
    list_display = ['period', 'forecast_date', 'predicted_revenue', 'accuracy', 'created_at']
    list_filter = ['period', 'forecast_date', 'created_at']
    readonly_fields = ['created_at', 'updated_at', 'predicted_revenue', 'confidence_interval_low', 'confidence_interval_high']
    fieldsets = (
        ('Prévisions', {'fields': ('period', 'forecast_date', 'predicted_revenue', 'predicted_invoices')}),
        ('Intervalle confiance', {'fields': ('confidence_interval_low', 'confidence_interval_high')}),
        ('Résultats réels', {'fields': ('actual_revenue', 'actual_invoices', 'accuracy')}),
        ('Historique', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(IntelligentAlert)
class IntelligentAlertAdmin(admin.ModelAdmin):
    list_display = ['alert_type', 'priority', 'title', 'is_acknowledged', 'created_at']
    list_filter = ['alert_type', 'priority', 'is_acknowledged', 'created_at']
    search_fields = ['title', 'description', 'related_invoice__invoice_number', 'related_client__name']
    readonly_fields = ['created_at', 'acknowledged_by', 'acknowledged_at']
    fieldsets = (
        ('Alerte', {'fields': ('alert_type', 'priority', 'title', 'description')}),
        ('Références', {'fields': ('related_invoice', 'related_client')}),
        ('Recommandation IA', {'fields': ('recommendation',)}),
        ('Statut', {'fields': ('is_acknowledged', 'acknowledged_by', 'acknowledged_at')}),
        ('Historique', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )


@admin.register(AccountingSynchronization)
class AccountingSynchronizationAdmin(admin.ModelAdmin):
    list_display = ['export_type', 'status', 'start_date', 'end_date', 'records_count', 'created_at']
    list_filter = ['export_type', 'status', 'created_at']
    search_fields = ['created_by', 'file_path']
    readonly_fields = ['created_at', 'completed_at', 'file_size', 'checksum']
    fieldsets = (
        ('Export', {'fields': ('export_type', 'status', 'records_count')}),
        ('Dates', {'fields': ('start_date', 'end_date')}),
        ('Fichier', {'fields': ('file_path', 'file_size', 'checksum')}),
        ('Erreurs', {'fields': ('error_message',)}),
        ('Historique', {'fields': ('created_by', 'created_at', 'completed_at'), 'classes': ('collapse',)}),
    )
