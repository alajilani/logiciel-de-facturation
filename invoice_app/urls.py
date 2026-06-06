from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

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
    path('categories/', views.CategorieProduitListView.as_view(), name='category-list'),
    path('categories/create/', views.CategorieProduitCreateView.as_view(), name='category-create'),
    path('categories/<int:pk>/update/', views.CategorieProduitUpdateView.as_view(), name='category-update'),
    path('categories/<int:pk>/delete/', views.CategorieProduitDeleteView.as_view(), name='category-delete'),
    
    # Invoices
    path('invoices/', views.InvoiceListView.as_view(), name='invoice-list'),
    path('invoices/create/', views.invoice_create_view, name='invoice-create'),
    path('invoices/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice-detail'),
    path('invoices/<int:pk>/update/', views.invoice_update_view, name='invoice-update'),
    path('invoices/<int:pk>/item/<int:item_id>/update/', views.invoice_update_item, name='invoice-update-item'),
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
    
    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/open/', views.notification_open, name='notification-open'),
    path('notifications/<int:pk>/mark-read/', views.notification_mark_read, name='notification-mark-read'),
    path('notifications/mark-all-read/', views.notifications_mark_all_read, name='notifications-mark-all-read'),
    path('notifications/<int:pk>/delete/', views.notification_delete, name='notification-delete'),

    # Email
    path('invoices/<int:pk>/send-email/', views.send_invoice_by_email, name='send-invoice-email'),
    path('invoices/<int:invoice_id>/send-reminder/', views.send_payment_reminder_view, name='send-reminder'),
    path('email-templates/', views.EmailTemplateListView.as_view(), name='email-template-list'),
    path('email-templates/<int:pk>/update/', views.EmailTemplateUpdateView.as_view(), name='email-template-update'),
    
    # Audit Log
    path('audit-log/', views.AuditLogListView.as_view(), name='audit-log'),
    
    # API
    path('api/product/<int:product_id>/price/', views.api_get_product_price, name='api-product-price'),
    path('api/invoice/summary/', views.api_invoice_summary, name='api-invoice-summary'),
    
    # ============================================================================
    # AUTHENTICATION
    # ============================================================================
    path('accounts/login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', LogoutView.as_view(next_page='login'), name='logout'),
]
