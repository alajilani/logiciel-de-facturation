from django.contrib import admin
from .models import Client, Product, CompanyInfo, Invoice, InvoiceItem, Payment, Quote, QuoteItem, Notification, EmailTemplate, AuditLog, ExchangeRate, SearchIndex, ArchiveLog

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
        ('Devise (Tier 2)', {'fields': ('currency', 'exchange_rate', 'original_currency')}),
        ('Détails', {'fields': ('subtotal', ('remise_percentage', 'remise_amount'), 
                                 ('rabais_percentage', 'rabais_amount'),
                                 ('escompte_percentage', 'escompte_amount'),
                                 'total_discount', 'tva_amount', 'total')}),
        ('Paiement', {'fields': ('payment_status', 'amount_paid', 'is_credit_note', 'credit_note_reason', 'original_invoice')}),
        ('Archivage (Tier 2)', {'fields': ('is_archived', 'archived_at', 'archived_by'), 'classes': ('collapse',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'amount', 'payment_date', 'payment_method', 'currency']
    list_filter = ['payment_date', 'payment_method', 'invoice__client', 'currency']
    search_fields = ['invoice__invoice_number', 'reference']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Informations', {'fields': ('invoice', 'amount', 'payment_date', 'payment_method', 'reference')}),
        ('Devise (Tier 2)', {'fields': ('currency',)}),
        ('Timestamps', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )


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
        ('Devise (Tier 2)', {'fields': ('currency', 'exchange_rate', 'original_currency')}),
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


# ============== TIER 2 Admin Interfaces ==============

@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ['from_currency', 'to_currency', 'rate', 'date', 'updated_at']
    list_filter = ['from_currency', 'to_currency', 'date']
    search_fields = ['from_currency', 'to_currency']
    ordering = ['-date']
    fieldsets = (
        ('Devises', {'fields': ('from_currency', 'to_currency')}),
        ('Taux', {'fields': ('rate', 'date')}),
    )


@admin.register(SearchIndex)
class SearchIndexAdmin(admin.ModelAdmin):
    list_display = ['content_type', 'document_number', 'client_name', 'date', 'updated_at']
    list_filter = ['content_type', 'date']
    search_fields = ['search_text', 'keywords', 'document_number', 'client_name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Contenu', {'fields': ('content_type', 'object_id')}),
        ('Recherche', {'fields': ('search_text', 'keywords')}),
        ('References', {'fields': ('document_number', 'client_name', 'amount', 'date')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(ArchiveLog)
class ArchiveLogAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'archived_by', 'archived_at', 'unarchived_at']
    list_filter = ['archived_at', 'unarchived_at']
    search_fields = ['invoice__invoice_number', 'archived_by', 'unarchived_by']
    readonly_fields = ['archived_at', 'unarchived_at']
    fieldsets = (
        ('Archivage', {'fields': ('invoice', 'archived_by', 'archived_at', 'reason')}),
        ('Restauration', {'fields': ('unarchived_by', 'unarchived_at', 'unarchive_reason')}),
    )

