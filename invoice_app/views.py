from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Sum, DecimalField, Count, F, Case, When
from django.db.models.functions import Coalesce, TruncMonth
from django.db import transaction
from datetime import datetime, timedelta
from decimal import Decimal
import json
from io import BytesIO
from collections import defaultdict
from django.views.decorators.http import require_POST

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side

from .models import Client, Product, Invoice, InvoiceItem, Payment, CompanyInfo, Quote, QuoteItem, Notification, EmailTemplate, AuditLog, CategorieProduit
from .forms import (
    ClientForm, ProductForm, InvoiceForm, 
    InvoiceItemForm, InvoiceDiscountForm, PaymentForm, InvoiceFilterForm,
    QuoteForm, QuoteItemForm, QuoteDiscountForm, QuoteFilterForm,
    EmailTemplateForm, SendEmailForm, NotificationFilterForm, CategorieProduitForm
)
from .email_utils import send_invoice_email, send_quote_email, send_payment_reminder, send_payment_thank_you
from .notification_service import refresh_due_soon_alerts
from django.conf import settings


# ============== Dashboard ==============

def dashboard(request):
    """Dashboard with statistics"""
    refresh_due_soon_alerts(days_threshold=3, max_invoices=50)

    total_clients = Client.objects.count()
    total_invoices = Invoice.objects.count()
    total_quotes = Quote.objects.count()
    total_revenue = Invoice.objects.filter(statut='PAYEE').aggregate(
        total=Coalesce(Sum('total_ttc'), Decimal('0'), output_field=DecimalField())
    )['total']
    pending_invoices = Invoice.objects.exclude(statut__in=['PAYEE', 'ANNULEE']).count()
    pending_quotes = Quote.objects.filter(status__in=['draft', 'sent']).count()
    
    recent_invoices = Invoice.objects.all()[:10]
    recent_quotes = Quote.objects.all()[:5]
    recent_notifications = Notification.objects.filter(
        lu=False,
        niveau__in=['HAUTE', 'MOYENNE'],
    ).order_by('-date_creation')[:5]
    company_info = CompanyInfo.objects.first()
    
    context = {
        'total_clients': total_clients,
        'total_invoices': total_invoices,
        'total_quotes': total_quotes,
        'total_revenue': total_revenue,
        'pending_invoices': pending_invoices,
        'pending_quotes': pending_quotes,
        'recent_invoices': recent_invoices,
        'recent_quotes': recent_quotes,
        'recent_notifications': recent_notifications,
        'company_info': company_info,
    }
    return render(request, 'invoice_app/dashboard.html', context)


def analytics(request):
    """Advanced analytics view with statistics"""
    period = request.GET.get('period', '12')  # 3, 6, 12 months or 'all'

    # Calculate date range
    if period == 'all':
        date_from = None
    else:
        months = int(period) if period.isdigit() else 12
        date_from = datetime.now().date() - timedelta(days=30 * months)

    today = datetime.now().date()

    # Base querysets
    invoices = Invoice.objects.exclude(is_credit_note=True)
    invoice_items = InvoiceItem.objects.all()

    if date_from:
        invoices = invoices.filter(date__gte=date_from)
        invoice_items = invoice_items.filter(invoice__date__gte=date_from)

    # ===== KEY PERFORMANCE INDICATORS =====
    total_invoices_count = invoices.count()

    total_revenue = invoices.filter(statut='PAYEE').aggregate(
        total=Coalesce(Sum('total_ttc'), Decimal('0'), output_field=DecimalField())
    )['total']

    pending_revenue = invoices.filter(statut__in=['ENVOYEE', 'PARTIELLEMENT_PAYEE', 'EN_RETARD']).aggregate(
        total=Coalesce(Sum('total_ttc'), Decimal('0'), output_field=DecimalField())
    )['total']

    average_invoice = (
        invoices.aggregate(avg=Coalesce(Sum('total_ttc'), Decimal('0'), output_field=DecimalField()))['avg']
        / total_invoices_count
    ) if total_invoices_count > 0 else Decimal('0')

    # Invoice counts by status
    paid_invoices = invoices.filter(statut='PAYEE').count()
    pending_invoices = invoices.filter(statut__in=['ENVOYEE', 'PARTIELLEMENT_PAYEE']).count()
    overdue_invoices = invoices.filter(statut='EN_RETARD').count()
    draft_invoices = invoices.filter(statut='BROUILLON').count()
    cancelled_invoices = invoices.filter(statut='ANNULEE').count()

    payment_rate = (paid_invoices / total_invoices_count * 100) if total_invoices_count > 0 else 0

    # Active clients (clients with at least one invoice in period)
    active_clients_count = invoices.values('client').distinct().count()
    total_clients = Client.objects.count()
    if date_from:
        new_clients = Client.objects.filter(created_at__gte=date_from).count()
    else:
        new_clients = total_clients

    # ===== MONTH-OVER-MONTH COMPARISON =====
    curr_month_start = today.replace(day=1)
    prev_month_end = curr_month_start - timedelta(days=1)
    prev_month_start = prev_month_end.replace(day=1)

    revenue_curr_month = Invoice.objects.exclude(is_credit_note=True).filter(
        statut='PAYEE', date__gte=curr_month_start, date__lte=today
    ).aggregate(total=Coalesce(Sum('total_ttc'), Decimal('0'), output_field=DecimalField()))['total']

    revenue_prev_month = Invoice.objects.exclude(is_credit_note=True).filter(
        statut='PAYEE', date__gte=prev_month_start, date__lte=prev_month_end
    ).aggregate(total=Coalesce(Sum('total_ttc'), Decimal('0'), output_field=DecimalField()))['total']

    if revenue_prev_month and revenue_prev_month > 0:
        revenue_variation_pct = float((revenue_curr_month - revenue_prev_month) / revenue_prev_month * 100)
    else:
        revenue_variation_pct = None

    # ===== TOP PRODUCTS =====
    top_products = invoice_items.values('produit_service__name').annotate(
        product_name=F('produit_service__name'),
        total_quantity=Sum('quantite'),
        total_revenue=Sum(F('quantite') * F('prix_unitaire_ht'), output_field=DecimalField())
    ).filter(product_name__isnull=False).order_by('-total_revenue')[:10]

    # ===== TOP CLIENTS =====
    top_clients = invoices.values('client__nom', 'client__id').annotate(
        total_amount=Sum('total_ttc'),
        invoice_count=Count('id')
    ).filter(client__isnull=False).order_by('-total_amount')[:10]

    # ===== REVENUE BY MONTH =====
    monthly_revenue = invoices.annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total=Sum('total_ttc'),
        count=Count('id')
    ).order_by('month')

    months_labels = []
    months_data = []
    for item in monthly_revenue:
        if item['month']:
            months_labels.append(item['month'].strftime('%b %Y'))
            months_data.append(float(item['total'] or 0))

    # ===== INVOICE STATUS CHART DATA =====
    status_map = {
        'PAYEE': 'Payées',
        'EN_RETARD': 'En retard',
        'ENVOYEE': 'Envoyées',
        'PARTIELLEMENT_PAYEE': 'Part. payées',
        'BROUILLON': 'Brouillons',
        'ANNULEE': 'Annulées',
    }
    status_labels = json.dumps(list(status_map.values()))
    status_data = json.dumps([
        paid_invoices, overdue_invoices, pending_invoices,
        invoices.filter(statut='PARTIELLEMENT_PAYEE').count(),
        draft_invoices, cancelled_invoices
    ])

    # ===== PAYMENT METHOD STATISTICS =====
    payment_method_display = dict(Invoice.PAYMENT_METHOD_CHOICES)
    raw_payment_methods = Payment.objects.filter(
        invoice__date__gte=date_from if date_from else '1900-01-01'
    ).values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')

    payment_methods = []
    pm_labels = []
    pm_data = []
    for pm in raw_payment_methods:
        code = pm['payment_method']
        label = payment_method_display.get(code, code)
        payment_methods.append({
            'label': label,
            'count': pm['count'],
            'total': pm['total'],
        })
        pm_labels.append(label)
        pm_data.append(float(pm['total'] or 0))

    payment_method_labels = json.dumps(pm_labels)
    payment_method_data = json.dumps(pm_data)

    # ===== OVERDUE INVOICES LIST =====
    overdue_list = Invoice.objects.exclude(is_credit_note=True).filter(
        statut='EN_RETARD'
    ).select_related('client').order_by('due_date')[:15]
    overdue_detail = []
    for inv in overdue_list:
        days_late = (today - inv.due_date).days if inv.due_date else 0
        overdue_detail.append({
            'invoice': inv,
            'days_late': days_late,
        })

    # ===== LOW STOCK PRODUCTS =====
    low_stock_products = Product.objects.filter(
        type_item='PRODUIT',
        suivre_stock=True,
    ).extra(where=['stock <= seuil_alerte']).order_by('stock')[:15]

    # ===== QUOTE STATISTICS =====
    quotes = Quote.objects.all()
    if date_from:
        quotes = quotes.filter(date__gte=date_from)

    total_quotes = quotes.count()
    accepted_quotes = quotes.filter(status='accepted').count()
    rejected_quotes = quotes.filter(status='rejected').count()
    draft_quotes = quotes.filter(status='draft').count()
    quote_conversion_rate = (accepted_quotes / total_quotes * 100) if total_quotes > 0 else 0

    quote_revenue = quotes.filter(converted_invoice__isnull=False).aggregate(
        total=Coalesce(Sum('total'), Decimal('0'), output_field=DecimalField())
    )['total']

    # ===== AVERAGE CLIENT VALUE =====
    avg_client_value = (total_revenue / active_clients_count) if active_clients_count > 0 else Decimal('0')

    # ===== DISCOUNT STATISTICS =====
    total_discounts = invoices.aggregate(
        total=Coalesce(Sum('total_remise'), Decimal('0'), output_field=DecimalField())
    )['total']
    sous_total_ht = invoices.aggregate(
        total=Coalesce(Sum('sous_total_ht'), Decimal('0'), output_field=DecimalField())
    )['total']
    discount_percentage = (float(total_discounts) / float(sous_total_ht) * 100) if sous_total_ht > 0 else 0

    # ===== BUSINESS-INTELLIGENCE KPIs =====
    # Taux d'impayés : factures en retard / total
    unpaid_rate_pct = (overdue_invoices / total_invoices_count * 100) if total_invoices_count > 0 else 0

    # Délai moyen de paiement (jours) : moyenne (premier paiement - date facture)
    paid_with_payment = Payment.objects.filter(
        invoice__statut='PAYEE',
    )
    if date_from:
        paid_with_payment = paid_with_payment.filter(invoice__date__gte=date_from)
    delays = []
    seen_inv = set()
    for pay in paid_with_payment.select_related('invoice').order_by('invoice_id', 'payment_date'):
        if pay.invoice_id in seen_inv or not pay.invoice or not pay.invoice.date or not pay.payment_date:
            continue
        seen_inv.add(pay.invoice_id)
        delta = (pay.payment_date - pay.invoice.date).days
        if delta >= 0:
            delays.append(delta)
    avg_payment_delay = round(sum(delays) / len(delays), 1) if delays else None

    # Meilleur client (premier de top_clients)
    top_clients_list = list(top_clients)
    if top_clients_list:
        best_client_name = top_clients_list[0].get('client__nom') or '—'
        best_client_amount = top_clients_list[0].get('total_amount') or Decimal('0')
    else:
        best_client_name = None
        best_client_amount = Decimal('0')

    # Produit / service le plus vendu (premier de top_products par CA)
    top_products_list = list(top_products)
    if top_products_list:
        best_product_name = top_products_list[0].get('product_name') or '—'
        best_product_qty = top_products_list[0].get('total_quantity') or 0
        best_product_revenue = top_products_list[0].get('total_revenue') or Decimal('0')
    else:
        best_product_name = None
        best_product_qty = 0
        best_product_revenue = Decimal('0')

    # Croissance mensuelle en € (écart absolu mois courant - mois précédent)
    revenue_growth_amount = (revenue_curr_month or Decimal('0')) - (revenue_prev_month or Decimal('0'))

    context = {
        # KPIs
        'total_revenue': total_revenue,
        'pending_revenue': pending_revenue,
        'average_invoice': average_invoice,
        'total_invoices_count': total_invoices_count,
        'paid_invoices': paid_invoices,
        'pending_invoices': pending_invoices,
        'overdue_invoices': overdue_invoices,
        'draft_invoices': draft_invoices,
        'cancelled_invoices': cancelled_invoices,
        'payment_rate': payment_rate,
        'active_clients_count': active_clients_count,
        'total_clients': total_clients,
        'new_clients': new_clients,
        'avg_client_value': avg_client_value,
        'revenue_curr_month': revenue_curr_month,
        'revenue_prev_month': revenue_prev_month,
        'revenue_variation_pct': revenue_variation_pct,

        # Top data
        'top_products': top_products,
        'top_clients': top_clients,

        # Charts data (JSON)
        'months_labels': json.dumps(months_labels),
        'months_data': json.dumps(months_data),
        'status_labels': status_labels,
        'status_data': status_data,
        'payment_method_labels': payment_method_labels,
        'payment_method_data': payment_method_data,

        # Tables
        'payment_methods': payment_methods,
        'overdue_detail': overdue_detail,
        'low_stock_products': low_stock_products,

        # Quote statistics
        'total_quotes': total_quotes,
        'accepted_quotes': accepted_quotes,
        'rejected_quotes': rejected_quotes,
        'draft_quotes': draft_quotes,
        'quote_conversion_rate': quote_conversion_rate,
        'quote_revenue': quote_revenue,

        # Discount statistics
        'total_discounts': total_discounts,
        'discount_percentage': discount_percentage,

        # Business intelligence KPIs
        'unpaid_rate_pct': unpaid_rate_pct,
        'avg_payment_delay': avg_payment_delay,
        'best_client_name': best_client_name,
        'best_client_amount': best_client_amount,
        'best_product_name': best_product_name,
        'best_product_qty': best_product_qty,
        'best_product_revenue': best_product_revenue,
        'revenue_growth_amount': revenue_growth_amount,

        # Period
        'period': period,
    }

    return render(request, 'invoice_app/analytics.html', context)


# ============== Client Views ==============

class ClientListView(ListView):
    model = Client
    template_name = 'invoice_app/client_list.html'
    context_object_name = 'clients'
    paginate_by = 50


class ClientDetailView(DetailView):
    model = Client
    template_name = 'invoice_app/client_detail.html'
    context_object_name = 'client'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invoices'] = self.object.invoices.all()
        return context


class ClientCreateView(CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'invoice_app/client_form.html'
    success_url = reverse_lazy('client-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Client créé avec succès!')
        return super().form_valid(form)


class ClientUpdateView(UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'invoice_app/client_form.html'
    success_url = reverse_lazy('client-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Client modifié avec succès!')
        return super().form_valid(form)


class ClientDeleteView(DeleteView):
    model = Client
    template_name = 'invoice_app/client_confirm_delete.html'
    success_url = reverse_lazy('client-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Client supprimé avec succès!')
        return super().delete(request, *args, **kwargs)


# ============== Product Views ==============

class ProductListView(ListView):
    model = Product
    template_name = 'invoice_app/product_list.html'
    context_object_name = 'products'
    paginate_by = 50


class ProductDetailView(DetailView):
    model = Product
    template_name = 'invoice_app/product_detail.html'
    context_object_name = 'product'


class ProductCreateView(CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'invoice_app/product_form.html'
    success_url = reverse_lazy('product-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Produit créé avec succès!')
        return super().form_valid(form)


class ProductUpdateView(UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'invoice_app/product_form.html'
    success_url = reverse_lazy('product-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Produit modifié avec succès!')
        return super().form_valid(form)


class ProductDeleteView(DeleteView):
    model = Product
    template_name = 'invoice_app/product_confirm_delete.html'
    success_url = reverse_lazy('product-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Produit supprimé avec succès!')
        return super().delete(request, *args, **kwargs)


class CategorieProduitListView(ListView):
    model = CategorieProduit
    template_name = 'invoice_app/categorieproduit_list.html'
    context_object_name = 'categories'
    paginate_by = 50


class CategorieProduitCreateView(CreateView):
    model = CategorieProduit
    form_class = CategorieProduitForm
    template_name = 'invoice_app/categorieproduit_form.html'
    success_url = reverse_lazy('category-list')

    def form_valid(self, form):
        messages.success(self.request, 'Catégorie créée avec succès!')
        return super().form_valid(form)


class CategorieProduitUpdateView(UpdateView):
    model = CategorieProduit
    form_class = CategorieProduitForm
    template_name = 'invoice_app/categorieproduit_form.html'
    success_url = reverse_lazy('category-list')

    def form_valid(self, form):
        messages.success(self.request, 'Catégorie modifiée avec succès!')
        return super().form_valid(form)


class CategorieProduitDeleteView(DeleteView):
    model = CategorieProduit
    template_name = 'invoice_app/categorieproduit_confirm_delete.html'
    success_url = reverse_lazy('category-list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Catégorie supprimée avec succès!')
        return super().delete(request, *args, **kwargs)


# ============== Invoice Views ==============

def get_next_invoice_number():
    """Generate next invoice number"""
    current_year = datetime.now().year
    latest_invoice = Invoice.objects.filter(
        invoice_number__startswith=f"{current_year}-"
    ).order_by('-invoice_number').first()
    
    if latest_invoice:
        last_number = int(latest_invoice.invoice_number.split('-')[1])
        next_number = last_number + 1
    else:
        next_number = 1
    
    return f"{current_year}-{next_number:03d}"


def calculate_tva(subtotal_after_discount, client_country):
    """Calculate TVA based on countries"""
    if client_country == "France":
        return subtotal_after_discount * Decimal('0.20')
    elif client_country in settings.EU_COUNTRIES:
        return Decimal('0')
    else:
        return Decimal('0')


class InvoiceListView(ListView):
    model = Invoice
    template_name = 'invoice_app/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Invoice.objects.select_related('client').exclude(is_credit_note=True)
        
        form = InvoiceFilterForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('client'):
                queryset = queryset.filter(client=form.cleaned_data['client'])
            if form.cleaned_data.get('statut'):
                queryset = queryset.filter(statut=form.cleaned_data['statut'])
            if form.cleaned_data.get('date_from'):
                queryset = queryset.filter(date__gte=form.cleaned_data['date_from'])
            if form.cleaned_data.get('date_to'):
                queryset = queryset.filter(date__lte=form.cleaned_data['date_to'])
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = InvoiceFilterForm(self.request.GET)
        return context


class InvoiceDetailView(DetailView):
    model = Invoice
    template_name = 'invoice_app/invoice_detail.html'
    context_object_name = 'invoice'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['payments'] = self.object.payments.all()
        context['company_info'] = CompanyInfo.objects.first()
        return context


def invoice_create_view(request):
    """Create new invoice with items"""
    from .email_utils import notify_invoice_created
    
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.invoice_number = get_next_invoice_number()
            invoice.statut = 'BROUILLON'
            invoice.save()
            
            # 🔔 CREATE REAL-TIME NOTIFICATION (Tier 4)
            try:
                if request.user.is_authenticated:
                    notify_invoice_created(request.user, invoice)
            except Exception as e:
                print(f"Notification error: {str(e)}")
            
            messages.success(request, 'Facture créée! Ajoutez maintenant les articles.')
            return redirect('invoice-update', pk=invoice.id)
    else:
        form = InvoiceForm()

    # Map client_id -> conditions_paiement for the frontend auto-due-date JS
    client_conditions_map = {
        str(c['id']): (c['conditions_paiement'] or 'IMMEDIAT')
        for c in Client.objects.values('id', 'conditions_paiement')
    }

    return render(request, 'invoice_app/invoice_form.html', {
        'form': form,
        'client_conditions_map': client_conditions_map,
    })


def invoice_update_view(request, pk):
    """Update invoice and manage items"""
    invoice = get_object_or_404(Invoice, pk=pk)
    is_locked = invoice.statut in ['VALIDEE', 'ENVOYEE', 'PARTIELLEMENT_PAYEE', 'PAYEE', 'EN_RETARD', 'ANNULEE']
    
    if request.method == 'POST':
        if 'save_draft' in request.POST:
            if is_locked:
                messages.error(request, 'Cette facture n\'est plus modifiable en brouillon.')
                return redirect('invoice-update', pk=invoice.id)
            form = InvoiceForm(request.POST, instance=invoice)
            if form.is_valid():
                invoice = form.save(commit=False)
                invoice.statut = 'BROUILLON'
                invoice.save()
                messages.success(request, 'Brouillon enregistré!')
                return redirect('invoice-update', pk=invoice.id)

        elif 'validate_invoice' in request.POST:
            if invoice.statut != 'BROUILLON':
                messages.warning(request, 'Seule une facture brouillon peut être validée.')
                return redirect('invoice-update', pk=invoice.id)
            if not invoice.items.exists():
                messages.error(request, 'Ajoutez au moins une ligne avant de valider la facture.')
                return redirect('invoice-update', pk=invoice.id)
            invoice.statut = 'VALIDEE'
            try:
                invoice.save()
                messages.success(request, 'Facture validée avec succès.')
            except Exception as e:
                messages.error(request, str(e))
            return redirect('invoice-update', pk=invoice.id)

        elif 'save_invoice' in request.POST:
            if is_locked:
                messages.error(request, 'Une facture validée ou envoyée ne peut plus être modifiée.')
                return redirect('invoice-update', pk=invoice.id)
            form = InvoiceForm(request.POST, instance=invoice)
            if form.is_valid():
                form.save()
                messages.success(request, 'Facture mise à jour!')
                return redirect('invoice-detail', pk=invoice.id)
        
        elif 'add_item' in request.POST:
            if is_locked:
                messages.error(request, 'Impossible d\'ajouter des lignes sur une facture non brouillon.')
                return redirect('invoice-update', pk=invoice.id)
            item_form = InvoiceItemForm(request.POST)
            if item_form.is_valid():
                item = item_form.save(commit=False)
                item.invoice = invoice
                if item.produit_service and not item.produit_service.can_allocate(item.quantite):
                    messages.error(
                        request,
                        f"Stock insuffisant. Disponible : {item.produit_service.stock} unités."
                    )
                    return redirect('invoice-update', pk=invoice.id)
                item.save()
                # use model calculation
                invoice.calculate_totals()
                invoice.save()
                messages.success(request, 'Article ajouté!')
                return redirect('invoice-update', pk=invoice.id)
        
        elif 'update_discount' in request.POST:
            if is_locked:
                messages.error(request, 'Impossible de modifier les remises sur une facture non brouillon.')
                return redirect('invoice-update', pk=invoice.id)
            discount_form = InvoiceDiscountForm(request.POST, instance=invoice)
            if discount_form.is_valid():
                discount_form.save()
                update_invoice_totals(invoice)
                messages.success(request, 'Réduction appliquée à la facture.')
                return redirect('invoice-update', pk=invoice.id)
            else:
                # Surface validation errors instead of failing silently.
                for field, errs in discount_form.errors.items():
                    for err in errs:
                        label = discount_form.fields[field].label if field in discount_form.fields else field
                        messages.error(request, f"Remise globale — {label}: {err}")
                return redirect('invoice-update', pk=invoice.id)

        elif 'add_payment' in request.POST:
            return redirect('add-payment', invoice_id=invoice.id)
    
    form = InvoiceForm(instance=invoice)
    item_form = InvoiceItemForm()
    discount_form = InvoiceDiscountForm(instance=invoice)
    
    products_qs = Product.objects.filter(statut='ACTIF', disponible_vente=True)
    products_json = {
        str(p.id): {
            'name': p.name,
            'description': p.description or p.name,
            'prix_unitaire_ht': float(p.prix_unitaire_ht),
            'prix_unitaire_ttc': float(p.prix_unitaire_ttc),
            'taux_tva': float(p.taux_tva),
            'unite': p.unite or '',
        }
        for p in products_qs
    }
    
    context = {
        'form': form,
        'item_form': item_form,
        'discount_form': discount_form,
        'invoice': invoice,
        'items': invoice.items.all(),
        'products': products_qs,
        'products_json': json.dumps(products_json),
        'is_locked': is_locked,
        'client_conditions_map': {
            str(c['id']): (c['conditions_paiement'] or 'IMMEDIAT')
            for c in Client.objects.values('id', 'conditions_paiement')
        },
    }
    return render(request, 'invoice_app/invoice_edit.html', context)


def invoice_update_item(request, pk, item_id):
    """Update a single invoice line item."""
    invoice = get_object_or_404(Invoice, pk=pk)
    item = get_object_or_404(InvoiceItem, pk=item_id, invoice=invoice)

    if invoice.statut != 'BROUILLON':
        messages.error(request, 'Impossible de modifier une ligne sur une facture non brouillon.')
        return redirect('invoice-update', pk=invoice.id)

    if request.method == 'POST':
        form = InvoiceItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            invoice.calculate_totals()
            invoice.save()
            messages.success(request, 'Ligne de facture modifiée.')
            return redirect('invoice-update', pk=invoice.id)
    else:
        form = InvoiceItemForm(instance=item)

    return render(request, 'invoice_app/invoice_item_form.html', {
        'form': form,
        'invoice': invoice,
        'item': item,
    })


def invoice_delete_item(request, pk, item_id):
    """Delete invoice item"""
    item = get_object_or_404(InvoiceItem, pk=item_id, invoice_id=pk)
    invoice = item.invoice
    if invoice.statut != 'BROUILLON':
        messages.error(request, 'Impossible de supprimer une ligne sur une facture non brouillon.')
        return redirect('invoice-update', pk=invoice.id)
    item.delete()
    invoice.calculate_totals()
    invoice.save()
    messages.success(request, 'Article supprimé!')
    return redirect('invoice-update', pk=invoice.id)


def update_invoice_totals(invoice):
    """Recalculate invoice totals"""
    # Delegate to model calculation
    invoice.calculate_totals()
    invoice.save()


class InvoiceDeleteView(DeleteView):
    model = Invoice
    template_name = 'invoice_app/invoice_confirm_delete.html'
    success_url = reverse_lazy('invoice-list')
    
    def delete(self, request, *args, **kwargs):
        invoice = self.get_object()
        if invoice.statut == 'PAYEE':
            messages.error(request, 'Une facture payée ne peut pas être supprimée.')
            return redirect('invoice-detail', pk=invoice.id)
        for item in invoice.items.select_related('produit_service').all():
            if item.produit_service and invoice.stock_movement_done:
                item.produit_service.increase_stock(item.quantite)
        messages.success(request, 'Facture supprimée!')
        return super().delete(request, *args, **kwargs)


# ============== Payment Views ==============

def add_payment(request, invoice_id):
    """Add payment to invoice"""
    from .email_utils import send_payment_confirmation, notify_payment_received
    
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.save()
            
            invoice.amount_paid += payment.amount
            invoice.update_statut_from_payment()
            invoice.save()
            
            # 🔔 CREATE REAL-TIME NOTIFICATION (Tier 4)
            try:
                if request.user.is_authenticated:
                    notify_payment_received(request.user, invoice, float(payment.amount))
            except Exception as e:
                print(f"Notification error: {str(e)}")
            
            # 📧 SEND PAYMENT CONFIRMATION EMAIL
            try:
                send_payment_confirmation(payment)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error("add_payment email error: %s", e)
            
            messages.success(request, f'Paiement de {payment.amount}€ enregistré avec succès.')
            return redirect('invoice-detail', pk=invoice.id)
    else:
        form = PaymentForm(initial={
            'payment_method': invoice.payment_method,
        })
        form.fields['amount'].initial = invoice.reste_a_payer
    
    return render(request, 'invoice_app/payment_form.html', {'form': form, 'invoice': invoice})


# ============== Export Views ==============

def build_invoice_pdf_bytes(invoice):
    """Generate the invoice PDF and return raw bytes (reusable for view + email)."""
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import KeepTogether
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm

    company = CompanyInfo.objects.first()
    client = invoice.client
    items = list(invoice.items.select_related('produit_service').all())
    payments = list(invoice.payments.all().order_by('payment_date')) if hasattr(invoice, 'payments') else []

    # ===== Numa palette =====
    VIOLET      = HexColor('#6366f1')
    INDIGO      = HexColor('#8b5cf6')
    INK         = HexColor('#0f172a')
    SLATE       = HexColor('#334155')
    MUTED       = HexColor('#64748b')
    SOFT        = HexColor('#94a3b8')
    BORDER      = HexColor('#e5e7eb')
    BORDER_SOFT = HexColor('#f1f5f9')
    BG_ROW      = HexColor('#fafbfd')
    BG_TINT     = HexColor('#f5f6ff')  # violet tint
    WHITE       = colors.white

    STATUS_STYLES = {
        'BROUILLON':            (HexColor('#64748b'), HexColor('#f1f5f9'), 'Brouillon'),
        'VALIDEE':              (HexColor('#4f46e5'), HexColor('#eef0ff'), 'Validée'),
        'ENVOYEE':              (HexColor('#b45309'), HexColor('#fef3c7'), 'Envoyée'),
        'PAYEE':                (HexColor('#15803d'), HexColor('#dcfce7'), 'Payée'),
        'PARTIELLEMENT_PAYEE':  (HexColor('#0e7490'), HexColor('#cffafe'), 'Partiellement payée'),
        'EN_RETARD':            (HexColor('#b91c1c'), HexColor('#fee2e2'), 'En retard'),
        'ANNULEE':              (HexColor('#6b7280'), HexColor('#f3f4f6'), 'Annulée'),
    }

    # ===== Helpers =====
    def money(amount):
        """French currency: 1 234,56 €"""
        try:
            v = float(amount or 0)
        except (TypeError, ValueError):
            v = 0.0
        s = f"{v:,.2f}"
        s = s.replace(',', ' ').replace('.', ',')
        return f"{s} €"

    def pct(value):
        try:
            v = float(value or 0)
            return f"{v:.0f} %" if v == int(v) else f"{v:.1f} %"
        except (TypeError, ValueError):
            return "0 %"

    def safe(text):
        t = (text or '').strip()
        return t if t and t not in ('—', 'N/A') else ''

    def para(txt, style):
        from xml.sax.saxutils import escape
        return Paragraph(escape(txt or ''), style)

    # ===== Styles =====
    styles = getSampleStyleSheet()
    BASE_FONT = 'Helvetica'
    BOLD_FONT = 'Helvetica-Bold'

    s_h1 = ParagraphStyle('h1', parent=styles['Normal'], fontName=BOLD_FONT,
                          fontSize=22, leading=24, textColor=INK, spaceAfter=0)
    s_brand = ParagraphStyle('brand', parent=styles['Normal'], fontName=BOLD_FONT,
                             fontSize=14, leading=16, textColor=INK)
    s_tagline = ParagraphStyle('tagline', parent=styles['Normal'], fontName=BASE_FONT,
                               fontSize=8.5, leading=11, textColor=MUTED)
    s_label = ParagraphStyle('label', parent=styles['Normal'], fontName=BOLD_FONT,
                             fontSize=7.5, leading=10, textColor=SOFT,
                             spaceAfter=2, alignment=TA_LEFT)
    s_label_r = ParagraphStyle('label_r', parent=s_label, alignment=TA_RIGHT)
    s_value = ParagraphStyle('value', parent=styles['Normal'], fontName=BASE_FONT,
                             fontSize=9.5, leading=12, textColor=SLATE)
    s_value_r = ParagraphStyle('value_r', parent=s_value, alignment=TA_RIGHT)
    s_value_b = ParagraphStyle('value_b', parent=s_value, fontName=BOLD_FONT, textColor=INK)
    s_value_b_r = ParagraphStyle('value_b_r', parent=s_value_b, alignment=TA_RIGHT)
    s_party_title = ParagraphStyle('party_title', parent=styles['Normal'], fontName=BOLD_FONT,
                                   fontSize=8, leading=10, textColor=VIOLET,
                                   spaceAfter=6, alignment=TA_LEFT)
    s_party_name = ParagraphStyle('party_name', parent=styles['Normal'], fontName=BOLD_FONT,
                                  fontSize=11, leading=14, textColor=INK, spaceAfter=2)
    s_party_line = ParagraphStyle('party_line', parent=styles['Normal'], fontName=BASE_FONT,
                                  fontSize=9, leading=12, textColor=SLATE)
    s_table_head = ParagraphStyle('thead', parent=styles['Normal'], fontName=BOLD_FONT,
                                  fontSize=8, leading=10, textColor=SOFT,
                                  alignment=TA_LEFT)
    s_table_head_r = ParagraphStyle('thead_r', parent=s_table_head, alignment=TA_RIGHT)
    s_item_desc = ParagraphStyle('item_desc', parent=styles['Normal'], fontName=BASE_FONT,
                                 fontSize=9, leading=12, textColor=SLATE)
    s_item_name = ParagraphStyle('item_name', parent=s_item_desc, fontName=BOLD_FONT, textColor=INK)
    s_item_num = ParagraphStyle('item_num', parent=s_item_desc, alignment=TA_RIGHT)
    s_item_num_b = ParagraphStyle('item_num_b', parent=s_item_num, fontName=BOLD_FONT, textColor=INK)
    s_status = ParagraphStyle('status', parent=styles['Normal'], fontName=BOLD_FONT,
                              fontSize=8, leading=10, alignment=TA_CENTER)
    s_total_label = ParagraphStyle('total_label', parent=styles['Normal'], fontName=BOLD_FONT,
                                   fontSize=10, leading=14, textColor=WHITE,
                                   alignment=TA_LEFT)
    s_total_value = ParagraphStyle('total_value', parent=styles['Normal'], fontName=BOLD_FONT,
                                   fontSize=18, leading=22, textColor=WHITE,
                                   alignment=TA_RIGHT)
    s_notes_title = ParagraphStyle('notes_t', parent=s_party_title, textColor=MUTED)
    s_notes = ParagraphStyle('notes', parent=s_party_line, textColor=MUTED, fontSize=8.5)

    # ===== Document =====
    buffer = BytesIO()
    PAGE_W, PAGE_H = A4
    LEFT = RIGHT = 18 * mm
    TOP = 20 * mm
    BOTTOM = 22 * mm
    CONTENT_W = PAGE_W - LEFT - RIGHT

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=LEFT, rightMargin=RIGHT,
        topMargin=TOP, bottomMargin=BOTTOM,
        title=f"Facture {invoice.invoice_number}",
        author=(company.name if company else 'Numa'),
    )

    story = []

    # ---------- HEADER ----------
    # Left: logo + brand
    brand_cells = []
    if company and company.logo:
        try:
            from reportlab.platypus import Image
            logo = Image(company.logo.path, width=30*mm, height=30*mm, kind='proportional')
            brand_cells.append([logo])
        except Exception:
            pass
    company_name = (company.name if company else 'Numa')
    brand_cells.append([para(company_name, s_brand)])
    brand_cells.append([para('Plateforme de facturation', s_tagline)])
    brand_table = Table(brand_cells, colWidths=[CONTENT_W * 0.5])
    brand_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    # Right: FACTURE big title + meta
    status_fg, status_bg, status_label = STATUS_STYLES.get(
        invoice.statut, (MUTED, BORDER_SOFT, invoice.get_statut_display())
    )

    meta_rows = [
        [para('FACTURE', s_h1), ''],
        ['', ''],
        [para('Numéro', s_label_r), para(invoice.invoice_number, s_value_b_r)],
        [para('Date', s_label_r), para(invoice.date.strftime('%d/%m/%Y'), s_value_r)],
        [para('Échéance', s_label_r), para(invoice.due_date.strftime('%d/%m/%Y') if invoice.due_date else '—', s_value_r)],
        [para('Statut', s_label_r),
         Table([[para(status_label, ParagraphStyle('st', parent=s_status, textColor=status_fg))]],
               colWidths=[28*mm],
               style=TableStyle([
                   ('BACKGROUND', (0, 0), (-1, -1), status_bg),
                   ('BOX', (0, 0), (-1, -1), 0.5, status_fg),
                   ('ROUNDEDCORNERS', [3, 3, 3, 3]),
                   ('LEFTPADDING', (0, 0), (-1, -1), 6),
                   ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                   ('TOPPADDING', (0, 0), (-1, -1), 3),
                   ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
               ]))],
    ]
    meta_table = Table(meta_rows, colWidths=[CONTENT_W * 0.27, CONTENT_W * 0.23])
    meta_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (1, 0)),
        ('ALIGN', (0, 0), (-1, 0), 'RIGHT'),
        ('ALIGN', (0, 1), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, 0), 0),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 2), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 2), (-1, -1), 2),
    ]))

    header = Table([[brand_table, meta_table]], colWidths=[CONTENT_W * 0.5, CONTENT_W * 0.5])
    header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(header)
    story.append(Spacer(1, 6))

    # Gradient-like divider (two thin lines stacked)
    divider = Table([['']], colWidths=[CONTENT_W], rowHeights=[2])
    divider.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), VIOLET),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(divider)
    story.append(Spacer(1, 18))

    # ---------- PARTIES (Émetteur / Destinataire) ----------
    def build_party(title, lines):
        """lines: list of strings (already filtered for empty)."""
        flow = [para(title, s_party_title)]
        if lines:
            flow.append(para(lines[0], s_party_name))
            for ln in lines[1:]:
                flow.append(para(ln, s_party_line))
        cell = Table([[item] for item in flow], colWidths=[CONTENT_W * 0.48])
        cell.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 14),
            ('RIGHTPADDING', (0, 0), (-1, -1), 14),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        return cell

    emetteur_lines = []
    if company:
        emetteur_lines.append(company.name or '')
        if safe(company.address):
            for ln in company.address.split('\n'):
                if safe(ln): emetteur_lines.append(ln.strip())
        cp_ville = ' '.join([x for x in [safe(company.postal_code), safe(company.city)] if x])
        if cp_ville: emetteur_lines.append(cp_ville)
        if safe(company.country): emetteur_lines.append(company.country)
        emetteur_lines.append('')
        if safe(company.phone): emetteur_lines.append(f"Tél. {company.phone}")
        if safe(company.email): emetteur_lines.append(company.email)
        if safe(company.siret): emetteur_lines.append(f"SIRET {company.siret}")
        if safe(company.tva_number): emetteur_lines.append(f"TVA {company.tva_number}")
    emetteur_lines = [l for l in emetteur_lines if l != '' or True]  # keep blank separator
    # Remove trailing blank if last is empty
    while emetteur_lines and emetteur_lines[-1] == '':
        emetteur_lines.pop()

    dest_lines = [client.nom or '']
    if safe(client.raison_sociale) and client.raison_sociale != client.nom:
        dest_lines.append(client.raison_sociale)
    if safe(client.adresse_facturation):
        for ln in client.adresse_facturation.split('\n'):
            if safe(ln): dest_lines.append(ln.strip())
    cp_ville = ' '.join([x for x in [safe(client.code_postal_facturation), safe(client.ville_facturation)] if x])
    if cp_ville: dest_lines.append(cp_ville)
    if safe(client.pays_facturation): dest_lines.append(client.pays_facturation)
    dest_lines.append('')
    if safe(client.contact_principal): dest_lines.append(client.contact_principal)
    if safe(client.email): dest_lines.append(client.email)
    if safe(client.telephone): dest_lines.append(f"Tél. {client.telephone}")
    if safe(client.siret_siren): dest_lines.append(f"SIRET {client.siret_siren}")
    if safe(client.numero_tva_intracommunautaire): dest_lines.append(f"TVA {client.numero_tva_intracommunautaire}")
    while dest_lines and dest_lines[-1] == '':
        dest_lines.pop()

    parties = Table(
        [[build_party('ÉMETTEUR', emetteur_lines),
          build_party('DESTINATAIRE', dest_lines)]],
        colWidths=[CONTENT_W * 0.5, CONTENT_W * 0.5],
    )
    parties.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), BG_ROW),
        ('BACKGROUND', (1, 0), (1, 0), BG_TINT),
        ('BOX', (0, 0), (0, 0), 0.5, BORDER),
        ('BOX', (1, 0), (1, 0), 0.5, HexColor('#c7d2fe')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
    ]))
    story.append(parties)
    story.append(Spacer(1, 22))

    # ---------- ITEMS TABLE ----------
    item_col_w = [
        CONTENT_W * 0.40,  # Description
        CONTENT_W * 0.08,  # Qté
        CONTENT_W * 0.15,  # PU HT
        CONTENT_W * 0.09,  # Remise
        CONTENT_W * 0.08,  # TVA
        CONTENT_W * 0.20,  # TTC
    ]
    rows = [[
        para('DESCRIPTION', s_table_head),
        para('QTÉ', s_table_head_r),
        para('PU HT', s_table_head_r),
        para('REMISE', s_table_head_r),
        para('TVA', s_table_head_r),
        para('MONTANT TTC', s_table_head_r),
    ]]
    for it in items:
        name = (it.produit_service.name if it.produit_service else '') or (it.description or '—')
        desc = it.description or ''
        if desc and desc.strip() != name.strip():
            desc_cell = [para(name, s_item_name), para(desc, s_item_desc)]
        else:
            desc_cell = [para(name, s_item_name)]
        desc_table = Table([[c] for c in desc_cell], colWidths=[item_col_w[0] - 16])
        desc_table.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        qte_text = f"{it.quantite:g}"
        if safe(it.unite):
            qte_text = f"{it.quantite:g} {it.unite}"
        rows.append([
            desc_table,
            para(qte_text, s_item_num),
            para(money(it.prix_unitaire_ht), s_item_num),
            para(pct(it.remise_pourcentage) if it.remise_pourcentage else '—', s_item_num),
            para(pct(it.taux_tva), s_item_num),
            para(money(it.total_ttc), s_item_num_b),
        ])

    items_table = Table(rows, colWidths=item_col_w, repeatRows=1)
    table_style = [
        # header
        ('BACKGROUND', (0, 0), (-1, 0), BG_ROW),
        ('LINEBELOW', (0, 0), (-1, 0), 1, BORDER),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        # body
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
        ('LINEBELOW', (0, 1), (-1, -1), 0.5, BORDER_SOFT),
    ]
    # Zebra rows
    for i in range(1, len(rows)):
        if i % 2 == 0:
            table_style.append(('BACKGROUND', (0, i), (-1, i), BG_ROW))
    items_table.setStyle(TableStyle(table_style))
    story.append(items_table)
    story.append(Spacer(1, 16))

    # ---------- TOTALS ----------
    totals_rows = []
    totals_rows.append([para('Sous-total HT', s_value), para(money(invoice.sous_total_ht), s_value_r)])
    if invoice.total_remise and float(invoice.total_remise) > 0:
        rem_label = 'Remise globale'
        if invoice.remise_globale_pourcentage and float(invoice.remise_globale_pourcentage) > 0:
            rem_label = f"Remise globale ({pct(invoice.remise_globale_pourcentage)})"
        totals_rows.append([
            para(rem_label, ParagraphStyle('rem', parent=s_value, textColor=HexColor('#b91c1c'))),
            para('− ' + money(invoice.total_remise),
                 ParagraphStyle('rem_r', parent=s_value_r, textColor=HexColor('#b91c1c'))),
        ])
    totals_rows.append([para('Total HT', s_value_b), para(money(invoice.total_ht), s_value_b_r)])
    totals_rows.append([para('TVA', s_value), para(money(invoice.total_tva), s_value_r)])

    totals_table = Table(totals_rows, colWidths=[CONTENT_W * 0.30, CONTENT_W * 0.25])
    totals_table.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -2), 0.4, BORDER_SOFT),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))

    # TOTAL TTC big block (violet)
    total_ttc_row = Table(
        [[para('TOTAL TTC', s_total_label), para(money(invoice.total_ttc), s_total_value)]],
        colWidths=[CONTENT_W * 0.30, CONTENT_W * 0.25],
    )
    total_ttc_row.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), VIOLET),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('LEFTPADDING', (0, 0), (-1, -1), 16),
        ('RIGHTPADDING', (0, 0), (-1, -1), 16),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
    ]))

    # Wrap totals + total_ttc in a right-aligned container
    totals_block = Table(
        [[totals_table], [Spacer(1, 4)], [total_ttc_row]],
        colWidths=[CONTENT_W * 0.55],
    )
    totals_block.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
    ]))
    totals_wrap = Table([['', totals_block]],
                        colWidths=[CONTENT_W * 0.45, CONTENT_W * 0.55])
    totals_wrap.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(KeepTogether(totals_wrap))
    story.append(Spacer(1, 22))

    # ---------- PAYMENTS ----------
    if payments:
        pay_title = Table([[para('PAIEMENTS ENREGISTRÉS', s_party_title)]], colWidths=[CONTENT_W])
        pay_title.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(pay_title)

        pay_rows = [[
            para('DATE', s_table_head),
            para('MODE', s_table_head),
            para('RÉFÉRENCE', s_table_head),
            para('MONTANT', s_table_head_r),
        ]]
        for p in payments:
            pay_rows.append([
                para(p.payment_date.strftime('%d/%m/%Y'), s_item_desc),
                para(p.get_payment_method_display() if p.payment_method else '—', s_item_desc),
                para(safe(p.reference) or '—', s_item_desc),
                para(money(p.amount), s_item_num_b),
            ])

        pay_w = [CONTENT_W * 0.18, CONTENT_W * 0.32, CONTENT_W * 0.30, CONTENT_W * 0.20]
        pay_table = Table(pay_rows, colWidths=pay_w, repeatRows=1)
        pstyle = [
            ('BACKGROUND', (0, 0), (-1, 0), BG_ROW),
            ('LINEBELOW', (0, 0), (-1, 0), 1, BORDER),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, 1), (-1, -1), 0.4, BORDER_SOFT),
        ]
        for i in range(1, len(pay_rows)):
            if i % 2 == 0:
                pstyle.append(('BACKGROUND', (0, i), (-1, i), BG_ROW))
        pay_table.setStyle(TableStyle(pstyle))
        story.append(pay_table)
        story.append(Spacer(1, 10))

        # Summary
        reste = float(invoice.reste_a_payer or 0)
        is_paid = reste <= 0.001
        summary_rows = [
            [para('Total payé', s_value), para(money(invoice.amount_paid), s_value_b_r)],
        ]
        summary_rows.append([
            para('Solde restant' if not is_paid else 'Solde',
                 ParagraphStyle('rem', parent=s_value_b,
                                textColor=HexColor('#15803d') if is_paid else HexColor('#b45309'))),
            para(money(invoice.reste_a_payer if not is_paid else 0),
                 ParagraphStyle('rem_r', parent=s_value_b_r,
                                textColor=HexColor('#15803d') if is_paid else HexColor('#b45309'))),
        ])
        summary_table = Table(summary_rows, colWidths=[CONTENT_W * 0.30, CONTENT_W * 0.25])
        summary_table.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, 0), 0.4, BORDER_SOFT),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        summary_wrap = Table([['', summary_table]],
                             colWidths=[CONTENT_W * 0.45, CONTENT_W * 0.55])
        summary_wrap.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(summary_wrap)
        story.append(Spacer(1, 18))

    # ---------- NOTES & MENTIONS (only if present) ----------
    notes_blocks = []
    if safe(invoice.notes):
        notes_blocks.append(('NOTES', invoice.notes))
    if safe(invoice.payment_terms):
        notes_blocks.append(('CONDITIONS DE PAIEMENT', invoice.payment_terms))
    if safe(invoice.legal_mentions):
        notes_blocks.append(('MENTIONS LÉGALES', invoice.legal_mentions))

    for title, body in notes_blocks:
        nt = Table([[para(title, s_notes_title)], [para(body, s_notes)]],
                   colWidths=[CONTENT_W])
        nt.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(nt)
        story.append(Spacer(1, 8))

    # ---------- FOOTER (drawn on each page) ----------
    def draw_footer(canvas, doc_):
        canvas.saveState()
        y = 14 * mm
        # Top separator
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.4)
        canvas.line(LEFT, y + 14, PAGE_W - RIGHT, y + 14)

        # Left: company line
        canvas.setFont(BOLD_FONT, 8)
        canvas.setFillColor(SLATE)
        left_parts = []
        if company:
            if company.name: left_parts.append(company.name)
            if safe(company.siret): left_parts.append(f"SIRET {company.siret}")
            if safe(company.tva_number): left_parts.append(f"TVA {company.tva_number}")
        canvas.drawString(LEFT, y + 4, '  ·  '.join(left_parts) if left_parts else '')

        # Second line: contact
        canvas.setFont(BASE_FONT, 7.5)
        canvas.setFillColor(MUTED)
        contact_parts = []
        if company:
            if safe(company.phone): contact_parts.append(company.phone)
            if safe(company.email): contact_parts.append(company.email)
            if safe(company.website): contact_parts.append(company.website)
        canvas.drawString(LEFT, y - 5, '  ·  '.join(contact_parts) if contact_parts else '')

        # Right: page number
        canvas.setFont(BASE_FONT, 7.5)
        canvas.setFillColor(SOFT)
        page_txt = f"Page {doc_.page}"
        canvas.drawRightString(PAGE_W - RIGHT, y + 4, page_txt)
        gen_txt = f"Facture générée par {company.name if company else 'Numa'}"
        canvas.drawRightString(PAGE_W - RIGHT, y - 5, gen_txt)
        canvas.restoreState()

    doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
    buffer.seek(0)
    return buffer.getvalue()


def export_invoice_pdf(request, pk):
    """HTTP view: download invoice as PDF."""
    invoice = get_object_or_404(Invoice, pk=pk)
    pdf_bytes = build_invoice_pdf_bytes(invoice)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Facture_{invoice.invoice_number}.pdf"'
    return response


def export_invoice_excel(request):
    """Export invoices as Excel"""
    wb = Workbook()
    ws = wb.active
    ws.title = "Factures"
    
    headers = ['Numéro', 'Client', 'Date', 'Montant HT', 'TVA', 'Total TTC', 'Statut', 'Montant payé']
    ws.append(headers)
    
    invoices = Invoice.objects.exclude(is_credit_note=True).select_related('client')
    for invoice in invoices:
        ws.append([
            invoice.invoice_number,
            invoice.client.nom,
            invoice.date.strftime('%d/%m/%Y'),
            f"{invoice.sous_total_ht:.2f}",
            f"{invoice.total_tva:.2f}",
            f"{invoice.total_ttc:.2f}",
            invoice.get_statut_display(),
            f"{invoice.amount_paid:.2f}",
        ])
    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="Factures.xlsx"'
    wb.save(response)
    return response


# ============== API Views ==============

def api_get_product_price(request, product_id):
    """API endpoint to get product price"""
    product = get_object_or_404(Product, pk=product_id, disponible_vente=True)
    return JsonResponse({
        'price': float(product.prix_unitaire_ht),
        'prix_unitaire_ttc': float(product.prix_unitaire_ttc),
        'taux_tva': float(product.taux_tva),
        'unite': product.unite or '',
        'description': product.description or product.name,
    })


def api_invoice_summary(request):
    """API endpoint to get invoice summary"""
    invoices = Invoice.objects.exclude(is_credit_note=True)
    total_invoices = invoices.count()
    total_revenue = invoices.aggregate(total=Sum('total_ttc'))['total'] or Decimal('0')
    paid = invoices.filter(statut='PAYEE').count()
    pending = invoices.filter(statut__in=['ENVOYEE', 'PARTIELLEMENT_PAYEE', 'EN_RETARD']).count()
    
    return JsonResponse({
        'total_invoices': total_invoices,
        'total_revenue': float(total_revenue),
        'paid': paid,
        'pending': pending,
    })


# ============== Quote Views ==============

def get_next_quote_number():
    """Generate next quote number"""
    current_year = datetime.now().year
    latest_quote = Quote.objects.filter(
        quote_number__startswith=f"DEV-{current_year}-"
    ).order_by('-quote_number').first()
    
    if latest_quote:
        last_number = int(latest_quote.quote_number.split('-')[2])
        next_number = last_number + 1
    else:
        next_number = 1
    
    return f"DEV-{current_year}-{next_number:03d}"


def update_quote_totals(quote):
    """Recalculate quote totals"""
    items = quote.items.all()
    quote.subtotal = sum(item.quantity * item.price for item in items)
    
    # Calculate total discount
    quote.remise_amount = quote.subtotal * (quote.remise_percentage / Decimal('100'))
    quote.rabais_amount = (quote.subtotal - quote.remise_amount) * (quote.rabais_percentage / Decimal('100'))
    
    subtotal_after_discount = quote.subtotal - quote.remise_amount - quote.rabais_amount
    
    quote.escompte_amount = subtotal_after_discount * (quote.escompte_percentage / Decimal('100'))
    quote.total_discount = quote.remise_amount + quote.rabais_amount + quote.escompte_amount
    
    final_subtotal = subtotal_after_discount - quote.escompte_amount
    quote.tva_amount = calculate_tva(final_subtotal, quote.client.pays_facturation)
    quote.total = final_subtotal + quote.tva_amount
    
    quote.save()


class QuoteListView(ListView):
    model = Quote
    template_name = 'invoice_app/quote_list.html'
    context_object_name = 'quotes'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Quote.objects.select_related('client')
        
        form = QuoteFilterForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('client'):
                queryset = queryset.filter(client=form.cleaned_data['client'])
            if form.cleaned_data.get('status'):
                queryset = queryset.filter(status=form.cleaned_data['status'])
            if form.cleaned_data.get('date_from'):
                queryset = queryset.filter(date__gte=form.cleaned_data['date_from'])
            if form.cleaned_data.get('date_to'):
                queryset = queryset.filter(date__lte=form.cleaned_data['date_to'])
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = QuoteFilterForm(self.request.GET)
        return context


class QuoteDetailView(DetailView):
    model = Quote
    template_name = 'invoice_app/quote_detail.html'
    context_object_name = 'quote'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['company_info'] = CompanyInfo.objects.first()
        return context


def quote_create_view(request):
    """Create new quote with items"""
    if request.method == 'POST':
        form = QuoteForm(request.POST)
        if form.is_valid():
            quote = form.save(commit=False)
            quote.quote_number = get_next_quote_number()
            quote.save()
            messages.success(request, 'Devis créé! Ajoutez maintenant les articles.')
            return redirect('quote-update', pk=quote.id)
    else:
        form = QuoteForm()
        form.fields['validity_date'].initial = datetime.now() + timedelta(days=30)
    
    return render(request, 'invoice_app/quote_form.html', {'form': form})


def quote_update_view(request, pk):
    """Update quote and manage items"""
    quote = get_object_or_404(Quote, pk=pk)
    
    if request.method == 'POST':
        if 'save_quote' in request.POST:
            form = QuoteForm(request.POST, instance=quote)
            if form.is_valid():
                form.save()
                messages.success(request, 'Devis mis à jour!')
                return redirect('quote-detail', pk=quote.id)
        
        elif 'add_item' in request.POST:
            item_form = QuoteItemForm(request.POST)
            if item_form.is_valid():
                item = item_form.save(commit=False)
                item.quote = quote
                item.save()
                update_quote_totals(quote)
                messages.success(request, 'Article ajouté!')
                return redirect('quote-update', pk=quote.id)
        
        elif 'update_discount' in request.POST:
            discount_form = QuoteDiscountForm(request.POST, instance=quote)
            if discount_form.is_valid():
                discount_form.save()
                update_quote_totals(quote)
                messages.success(request, 'Réductions mises à jour!')
                return redirect('quote-update', pk=quote.id)
    
    form = QuoteForm(instance=quote)
    item_form = QuoteItemForm()
    discount_form = QuoteDiscountForm(instance=quote)
    
    context = {
        'form': form,
        'item_form': item_form,
        'discount_form': discount_form,
        'quote': quote,
        'items': quote.items.all(),
    }
    return render(request, 'invoice_app/quote_edit.html', context)


def quote_delete_item(request, pk):
    """Delete quote item"""
    item = get_object_or_404(QuoteItem, pk=pk)
    quote = item.quote
    item.delete()
    update_quote_totals(quote)
    messages.success(request, 'Article supprimé!')
    return redirect('quote-update', pk=quote.id)


class QuoteDeleteView(DeleteView):
    model = Quote
    template_name = 'invoice_app/quote_confirm_delete.html'
    success_url = reverse_lazy('quote-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Devis supprimé!')
        return super().delete(request, *args, **kwargs)


def quote_to_invoice(request, pk):
    """Convert quote to invoice"""
    from .email_utils import notify_invoice_created
    
    quote = get_object_or_404(Quote, pk=pk)
    
    if quote.status == 'converted':
        messages.warning(request, 'Ce devis a déjà été converti en facture!')
        return redirect('quote-detail', pk=quote.id)
    
    with transaction.atomic():
        quote_items = list(quote.items.select_related('product').all())
        for quote_item in quote_items:
            if quote_item.product and not quote_item.product.can_allocate(quote_item.quantity):
                messages.error(
                    request,
                    f"Stock insuffisant pour convertir le devis: {quote_item.product.name}. Stock disponible: {quote_item.product.stock}"
                )
                return redirect('quote-detail', pk=quote.id)

        # Create invoice from quote
        invoice = Invoice.objects.create(
            invoice_number=get_next_invoice_number(),
            client=quote.client,
            date=datetime.now(),
            due_date=datetime.now() + timedelta(days=30),
        )

        # Copy items from quote to invoice
        for quote_item in quote_items:
            InvoiceItem.objects.create(
                invoice=invoice,
                description=quote_item.description,
                quantite=quote_item.quantity,
                prix_unitaire_ht=quote_item.price,
                produit_service=quote_item.product,
            )
            if quote_item.product:
                quote_item.product.decrease_stock(quote_item.quantity)

        # Update quote status
        quote.status = 'converted'
        quote.converted_invoice = invoice
        quote.save()
    
    # 🔔 CREATE REAL-TIME NOTIFICATION (Tier 4)
    try:
        if request.user.is_authenticated:
            notify_invoice_created(request.user, invoice)
    except Exception as e:
        print(f"Notification error: {str(e)}")
    
    messages.success(request, f'Devis converti en facture {invoice.invoice_number}!')
    return redirect('invoice-detail', pk=invoice.id)


def quote_change_status(request, pk, status):
    """Change quote status"""
    quote = get_object_or_404(Quote, pk=pk)
    valid_statuses = dict(Quote.STATUS_CHOICES).keys()
    
    if status not in valid_statuses:
        messages.error(request, 'Statut invalide!')
        return redirect('quote-detail', pk=quote.id)
    
    quote.status = status
    quote.save()
    messages.success(request, f'Statut du devis mis à jour: {quote.get_status_display()}')
    return redirect('quote-detail', pk=quote.id)


def export_quote_pdf(request, pk):
    """Export quote as PDF"""
    quote = get_object_or_404(Quote, pk=pk)
    company_info = CompanyInfo.objects.first()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Company header
    if company_info:
        company_data = [
            [Paragraph(f"<b>{company_info.name}</b>", styles['Heading1'])],
            [Paragraph(company_info.address or '', styles['Normal'])],
            [Paragraph(f"Tel: {company_info.phone}", styles['Normal'])],
            [Paragraph(f"Email: {company_info.email}", styles['Normal'])],
        ]
        company_table = Table(company_data, colWidths=[6*inch])
        elements.append(company_table)
    
    elements.append(Spacer(1, 0.3*inch))
    
    # Quote title
    elements.append(Paragraph(f"<b>DEVIS {quote.quote_number}</b>", styles['Heading2']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Quote info
    info_data = [
        ['Date:', quote.date.strftime('%d/%m/%Y')],
        ['Validité:', quote.validity_date.strftime('%d/%m/%Y')],
        ['Statut:', quote.get_status_display()],
    ]
    info_table = Table(info_data, colWidths=[2*inch, 2*inch])
    elements.append(info_table)
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Client info
    elements.append(Paragraph("<b>Client:</b>", styles['Normal']))
    client_data = [
        [quote.client.nom],
        [quote.client.adresse_complete_livraison or ''],
        [f"{quote.client.pays_facturation}"],
    ]
    client_table = Table(client_data, colWidths=[3*inch])
    elements.append(client_table)
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Items table
    items_data = [['Description', 'Quantité', 'Prix U.', 'Total']]
    for item in quote.items.all():
        items_data.append([
            item.description,
            str(item.quantity),
            f"{item.price:.2f}€",
            f"{item.total:.2f}€",
        ])
    
    items_table = Table(items_data, colWidths=[3*inch, 1*inch, 1*inch, 1*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(items_table)
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Totals
    totals_data = [
        ['Sous-total:', f"{quote.subtotal:.2f}€"],
        ['Remise:', f"-{quote.remise_amount:.2f}€"],
        ['Rabais:', f"-{quote.rabais_amount:.2f}€"],
        ['Escompte:', f"-{quote.escompte_amount:.2f}€"],
        ['TVA (20%):', f"{quote.tva_amount:.2f}€"],
        ['<b>TOTAL TTC:</b>', f"<b>{quote.total:.2f}€</b>"],
    ]
    totals_table = Table(totals_data, colWidths=[3*inch, 1.5*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(totals_table)
    
    if quote.notes:
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph(f"<b>Notes:</b> {quote.notes}", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Devis_{quote.quote_number}.pdf"'
    return response


# ============== Email & Notification Views ==============

class NotificationListView(ListView):
    model = Notification
    template_name = 'invoice_app/realtime_notifications_list.html'
    context_object_name = 'notifications'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Notification.objects.select_related('client', 'invoice', 'quote')
        
        form = NotificationFilterForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('type_notification'):
                queryset = queryset.filter(type_notification=form.cleaned_data['type_notification'])
            if form.cleaned_data.get('niveau'):
                queryset = queryset.filter(niveau=form.cleaned_data['niveau'])
            if form.cleaned_data.get('lu') == 'lu':
                queryset = queryset.filter(lu=True)
            if form.cleaned_data.get('lu') == 'non_lu':
                queryset = queryset.filter(lu=False)
            if form.cleaned_data.get('client'):
                queryset = queryset.filter(client=form.cleaned_data['client'])
            if form.cleaned_data.get('date_from'):
                queryset = queryset.filter(date_creation__date__gte=form.cleaned_data['date_from'])
            if form.cleaned_data.get('date_to'):
                queryset = queryset.filter(date_creation__date__lte=form.cleaned_data['date_to'])
        
        return queryset.order_by('-date_creation')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = NotificationFilterForm(self.request.GET)
        context['unread_count'] = Notification.objects.filter(lu=False).count()
        return context


@require_POST
def notification_mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    notification.lu = True
    notification.save(update_fields=['lu', 'status'])
    messages.success(request, 'Notification marquée comme lue.')
    return redirect('notification-list')


@require_POST
def notifications_mark_all_read(request):
    Notification.objects.filter(lu=False).update(lu=True, status='read')
    messages.success(request, 'Toutes les notifications ont été marquées comme lues.')
    return redirect('notification-list')


@require_POST
def notification_delete(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    notification.delete()
    messages.success(request, 'Notification supprimée.')
    return redirect('notification-list')


def notification_open(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    if not notification.lu:
        notification.lu = True
        notification.save(update_fields=['lu', 'status'])

    if notification.lien:
        return redirect(notification.lien)
    return redirect('notification-list')


def send_invoice_by_email(request, pk):
    """Send invoice to client by email"""
    from .email_utils import notify_invoice_sent
    
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if request.method == 'POST':
        form = SendEmailForm(request.POST)
        if form.is_valid():
            success = send_invoice_email(
                invoice=invoice,
                custom_message=form.cleaned_data.get('custom_message', ''),
                send_attachment=form.cleaned_data.get('attach_pdf', True)
            )
            
            if success:
                # 🔔 CREATE REAL-TIME NOTIFICATION (Tier 4)
                try:
                    if request.user.is_authenticated:
                        notify_invoice_sent(request.user, invoice)
                except Exception as e:
                    print(f"Notification error: {str(e)}")
                
                messages.success(request, f'Email envoyé avec succès à {invoice.client.email}!')
            else:
                messages.error(request, 'Erreur lors de l\'envoi de l\'email.')
            
            return redirect('invoice-detail', pk=invoice.id)
    else:
        form = SendEmailForm(initial={'recipient_email': invoice.client.email})
    
    return render(request, 'invoice_app/send_email.html', {
        'form': form,
        'invoice': invoice,
        'document_type': 'facture'
    })


def send_quote_by_email(request, pk):
    """Send quote to client by email"""
    quote = get_object_or_404(Quote, pk=pk)
    
    if request.method == 'POST':
        form = SendEmailForm(request.POST)
        if form.is_valid():
            success = send_quote_email(
                quote=quote,
                custom_message=form.cleaned_data.get('custom_message', '')
            )
            
            if success:
                messages.success(request, 'Email envoyé avec succès!')
                # Update quote status to 'sent'
                quote.status = 'sent'
                quote.save()
            else:
                messages.error(request, 'Erreur lors de l\'envoi de l\'email.')
            
            return redirect('quote-detail', pk=quote.id)
    else:
        form = SendEmailForm(initial={'recipient_email': quote.client.email})
    
    return render(request, 'invoice_app/send_email.html', {
        'form': form,
        'quote': quote,
        'document_type': 'devis'
    })


def send_payment_reminder_view(request, invoice_id):
    """Send payment reminder for invoice"""
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    
    if request.method == 'POST':
        success = send_payment_reminder(invoice)
        
        if success:
            messages.success(request, 'Rappel envoyé au client!')
        else:
            messages.error(request, 'Erreur lors de l\'envoi du rappel.')
        
        return redirect('invoice-detail', pk=invoice.id)
    
    return render(request, 'invoice_app/send_reminder.html', {'invoice': invoice})


class EmailTemplateListView(ListView):
    model = EmailTemplate
    template_name = 'invoice_app/email_template_list.html'
    context_object_name = 'templates'


class EmailTemplateUpdateView(UpdateView):
    model = EmailTemplate
    form_class = EmailTemplateForm
    template_name = 'invoice_app/email_template_form.html'
    success_url = reverse_lazy('email-template-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Template mis à jour!')
        return super().form_valid(form)


# ============== Audit Log Views ==============

class AuditLogListView(LoginRequiredMixin, ListView):
    model = AuditLog
    template_name = 'invoice_app/audit_log_list.html'
    context_object_name = 'audit_logs'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = AuditLog.objects.all()
        
        # Filter by action
        action = self.request.GET.get('action')
        if action and action != '':
            queryset = queryset.filter(action=action)
        
        # Filter by model
        model = self.request.GET.get('model')
        if model and model != '':
            queryset = queryset.filter(model=model)
        
        # Filter by user
        user = self.request.GET.get('user')
        if user and user != '':
            queryset = queryset.filter(user__icontains=user)
        
        # Filter by date range
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(timestamp__date__gte=date_from)
        
        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(timestamp__date__lte=date_to)
        
        return queryset.order_by('-timestamp')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['actions'] = dict(AuditLog.ACTION_CHOICES)
        context['models'] = dict(AuditLog.MODEL_CHOICES)
        return context
