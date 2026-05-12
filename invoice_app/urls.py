from django.urls import path
from . import views
from . import tier2_views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('analytics/', views.analytics, name='analytics'),
    
    # Clients
    path('clients/', views.ClientListView.as_view(), name='client-list'),
    path('clients/create/', views.ClientCreateView.as_view(), name='client-create'),
    path('clients/<int:pk>/', views.ClientDetailView.as_view(), name='client-detail'),
    path('clients/<int:pk>/update/', views.ClientUpdateView.as_view(), name='client-update'),
    path('clients/<int:pk>/delete/', views.ClientDeleteView.as_view(), name='client-delete'),
    
    # Products
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/create/', views.ProductCreateView.as_view(), name='product-create'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('products/<int:pk>/update/', views.ProductUpdateView.as_view(), name='product-update'),
    path('products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product-delete'),
    
    # Invoices
    path('invoices/', views.InvoiceListView.as_view(), name='invoice-list'),
    path('invoices/create/', views.invoice_create_view, name='invoice-create'),
    path('invoices/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice-detail'),
    path('invoices/<int:pk>/update/', views.invoice_update_view, name='invoice-update'),
    path('invoices/<int:pk>/delete/', views.InvoiceDeleteView.as_view(), name='invoice-delete'),
    path('invoices/<int:pk>/item/delete/<int:item_id>/', views.invoice_delete_item, name='invoice-delete-item'),
    
    # Payments
    path('invoices/<int:invoice_id>/payment/add/', views.add_payment, name='add-payment'),
    
    # Export
    path('invoices/<int:pk>/export/pdf/', views.export_invoice_pdf, name='export-pdf'),
    path('invoices/export/excel/', views.export_invoice_excel, name='export-excel'),
    
    # Quotes (Devis)
    path('quotes/', views.QuoteListView.as_view(), name='quote-list'),
    path('quotes/create/', views.quote_create_view, name='quote-create'),
    path('quotes/<int:pk>/', views.QuoteDetailView.as_view(), name='quote-detail'),
    path('quotes/<int:pk>/update/', views.quote_update_view, name='quote-update'),
    path('quotes/<int:pk>/delete/', views.QuoteDeleteView.as_view(), name='quote-delete'),
    path('quotes/<int:pk>/item/delete/<int:item_id>/', views.quote_delete_item, name='quote-delete-item'),
    path('quotes/<int:pk>/to-invoice/', views.quote_to_invoice, name='quote-to-invoice'),
    path('quotes/<int:pk>/status/<str:status>/', views.quote_change_status, name='quote-change-status'),
    path('quotes/<int:pk>/export/pdf/', views.export_quote_pdf, name='export-quote-pdf'),
    path('quotes/<int:pk>/send-email/', views.send_quote_by_email, name='send-quote-email'),
    
    # Email & Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('invoices/<int:pk>/send-email/', views.send_invoice_by_email, name='send-invoice-email'),
    path('invoices/<int:invoice_id>/send-reminder/', views.send_payment_reminder_view, name='send-reminder'),
    path('email-templates/', views.EmailTemplateListView.as_view(), name='email-template-list'),
    path('email-templates/<int:pk>/update/', views.EmailTemplateUpdateView.as_view(), name='email-template-update'),
    
    # Audit Log
    path('audit-log/', views.AuditLogListView.as_view(), name='audit-log'),
    
    # Company Info
    path('settings/company-info/', views.company_info_view, name='company-info'),
    
    # API
    path('api/product/<int:product_id>/price/', views.api_get_product_price, name='api-product-price'),
    path('api/invoice/summary/', views.api_invoice_summary, name='api-invoice-summary'),
    
    # ============== TIER 2: Multi-Currency, Search, Archive ==============
    
    # Multi-Currency
    path('exchange-rates/', tier2_views.exchange_rates_list, name='exchange-rates-list'),
    path('invoices/<int:invoice_id>/convert-currency/', tier2_views.invoice_convert_currency, name='invoice-convert-currency'),
    
    # Advanced Search
    path('search/', tier2_views.advanced_search, name='advanced-search'),
    
    # Invoice Archiving
    path('invoices/<int:invoice_id>/archive/', tier2_views.invoice_archive, name='invoice-archive'),
    path('invoices/<int:invoice_id>/unarchive/', tier2_views.invoice_unarchive, name='invoice-unarchive'),
    path('archived-invoices/', tier2_views.archived_invoices_list, name='archived-invoices-list'),
    path('invoices/<int:invoice_id>/archive-logs/', tier2_views.archive_logs_detail, name='archive-logs-detail'),
]

