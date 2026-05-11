from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Sum, DecimalField, Count, F, Case, When
from django.db.models.functions import Coalesce, TruncMonth
from datetime import datetime, timedelta
from decimal import Decimal
import json
from io import BytesIO
from collections import defaultdict

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side

from .models import Client, Product, Invoice, InvoiceItem, Payment, CompanyInfo, Quote, QuoteItem, Notification, EmailTemplate, AuditLog
from .forms import (
    ClientForm, ProductForm, CompanyInfoForm, InvoiceForm, 
    InvoiceItemForm, InvoiceDiscountForm, PaymentForm, InvoiceFilterForm,
    QuoteForm, QuoteItemForm, QuoteDiscountForm, QuoteFilterForm,
    EmailTemplateForm, SendEmailForm, NotificationFilterForm
)
from .email_utils import send_invoice_email, send_quote_email, send_payment_reminder, send_payment_thank_you
from django.conf import settings


# ============== Dashboard ==============

def dashboard(request):
    """Dashboard with statistics"""
    total_clients = Client.objects.count()
    total_invoices = Invoice.objects.count()
    total_quotes = Quote.objects.count()
    total_revenue = Invoice.objects.filter(payment_status='paid').aggregate(
        total=Coalesce(Sum('total'), Decimal('0'), output_field=DecimalField())
    )['total']
    pending_invoices = Invoice.objects.filter(payment_status__in=['pending', 'partial']).count()
    pending_quotes = Quote.objects.filter(status__in=['draft', 'sent']).count()
    
    recent_invoices = Invoice.objects.all()[:10]
    recent_quotes = Quote.objects.all()[:5]
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
    
    # Base querysets
    invoices = Invoice.objects.exclude(is_credit_note=True)
    invoice_items = InvoiceItem.objects.all()
    
    if date_from:
        invoices = invoices.filter(date__gte=date_from)
        invoice_items = invoice_items.filter(invoice__date__gte=date_from)
    
    # ===== KEY PERFORMANCE INDICATORS =====
    
    # Total revenue and statistics
    total_revenue = invoices.filter(payment_status='paid').aggregate(
        total=Coalesce(Sum('total'), Decimal('0'), output_field=DecimalField())
    )['total']
    
    pending_revenue = invoices.filter(payment_status__in=['pending', 'partial']).aggregate(
        total=Coalesce(Sum('total'), Decimal('0'), output_field=DecimalField())
    )['total']
    
    average_invoice = invoices.aggregate(
        avg=Coalesce(Sum('total'), Decimal('0'), output_field=DecimalField()) / 
            Case(When(id__isnull=False, then=Count('id')), default=1)
    )['avg'] if invoices.exists() else Decimal('0')
    
    # Payment statistics
    paid_invoices = invoices.filter(payment_status='paid').count()
    pending_invoices = invoices.filter(payment_status__in=['pending', 'partial']).count()
    overdue_invoices = invoices.filter(
        payment_status__in=['pending', 'partial'],
        due_date__lt=datetime.now().date()
    ).count()
    
    payment_rate = (paid_invoices / invoices.count() * 100) if invoices.count() > 0 else 0
    
    # ===== TOP PRODUCTS =====
    top_products = invoice_items.values('product__name').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('price'), output_field=DecimalField())
    ).order_by('-total_revenue')[:10]
    
    # ===== TOP CLIENTS =====
    top_clients = invoices.values('client__name', 'client__id').annotate(
        total_amount=Sum('total'),
        invoice_count=Count('id')
    ).order_by('-total_amount')[:10]
    
    # ===== REVENUE BY MONTH =====
    monthly_revenue = invoices.annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total=Sum('total'),
        count=Count('id')
    ).order_by('month')
    
    # Format monthly data for charts
    months_labels = []
    months_data = []
    for item in monthly_revenue:
        if item['month']:
            months_labels.append(item['month'].strftime('%b %Y'))
            months_data.append(float(item['total'] or 0))
    
    # ===== QUOTE STATISTICS =====
    quotes = Quote.objects.all()
    if date_from:
        quotes = quotes.filter(date__gte=date_from)
    
    total_quotes = quotes.count()
    accepted_quotes = quotes.filter(status='accepted').count()
    rejected_quotes = quotes.filter(status='rejected').count()
    quote_conversion_rate = (accepted_quotes / total_quotes * 100) if total_quotes > 0 else 0
    
    quote_revenue = quotes.filter(converted_invoice__isnull=False).aggregate(
        total=Coalesce(Sum('total'), Decimal('0'), output_field=DecimalField())
    )['total']
    
    # ===== CLIENT STATISTICS =====
    total_clients = Client.objects.count()
    if date_from:
        new_clients = Client.objects.filter(created_at__gte=date_from).count()
    else:
        new_clients = total_clients
    
    # Average client value
    avg_client_value = invoices.values('client').annotate(
        total=Sum('total')
    ).aggregate(
        avg=Coalesce(Sum('total') / Case(When(client__isnull=False, then=Count('client', distinct=True)), default=1),
                    Decimal('0'), output_field=DecimalField())
    )['avg']
    
    # ===== PAYMENT STATISTICS =====
    payment_methods = Payment.objects.filter(
        invoice__date__gte=date_from if date_from else '1900-01-01'
    ).values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # ===== DISCOUNT STATISTICS =====
    total_discounts = invoices.aggregate(
        total=Coalesce(Sum('total_discount'), Decimal('0'), output_field=DecimalField())
    )['total']
    
    discount_percentage = (total_discounts / invoices.aggregate(
        total=Coalesce(Sum('subtotal'), Decimal('0'), output_field=DecimalField())
    )['total'] * 100) if invoices.aggregate(
        total=Coalesce(Sum('subtotal'), Decimal('0'), output_field=DecimalField())
    )['total'] > 0 else 0
    
    context = {
        # KPIs
        'total_revenue': total_revenue,
        'pending_revenue': pending_revenue,
        'average_invoice': average_invoice,
        'paid_invoices': paid_invoices,
        'pending_invoices': pending_invoices,
        'overdue_invoices': overdue_invoices,
        'payment_rate': payment_rate,
        
        # Top data
        'top_products': top_products,
        'top_clients': top_clients,
        
        # Charts data (JSON)
        'months_labels': json.dumps(months_labels),
        'months_data': json.dumps(months_data),
        
        # Quote statistics
        'total_quotes': total_quotes,
        'accepted_quotes': accepted_quotes,
        'rejected_quotes': rejected_quotes,
        'quote_conversion_rate': quote_conversion_rate,
        'quote_revenue': quote_revenue,
        
        # Client statistics
        'total_clients': total_clients,
        'new_clients': new_clients,
        'avg_client_value': avg_client_value,
        
        # Payment statistics
        'payment_methods': payment_methods,
        
        # Discount statistics
        'total_discounts': total_discounts,
        'discount_percentage': discount_percentage,
        
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
            if form.cleaned_data.get('payment_status'):
                queryset = queryset.filter(payment_status=form.cleaned_data['payment_status'])
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
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.invoice_number = get_next_invoice_number()
            invoice.save()
            messages.success(request, 'Facture créée! Ajoutez maintenant les articles.')
            return redirect('invoice-update', pk=invoice.id)
    else:
        form = InvoiceForm()
        form.fields['due_date'].initial = datetime.now() + timedelta(days=30)
    
    return render(request, 'invoice_app/invoice_form.html', {'form': form})


def invoice_update_view(request, pk):
    """Update invoice and manage items"""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if request.method == 'POST':
        if 'save_invoice' in request.POST:
            form = InvoiceForm(request.POST, instance=invoice)
            if form.is_valid():
                form.save()
                messages.success(request, 'Facture mise à jour!')
                return redirect('invoice-detail', pk=invoice.id)
        
        elif 'add_item' in request.POST:
            item_form = InvoiceItemForm(request.POST)
            if item_form.is_valid():
                item = item_form.save(commit=False)
                item.invoice = invoice
                item.save()
                update_invoice_totals(invoice)
                messages.success(request, 'Article ajouté!')
                return redirect('invoice-update', pk=invoice.id)
        
        elif 'update_discount' in request.POST:
            discount_form = InvoiceDiscountForm(request.POST, instance=invoice)
            if discount_form.is_valid():
                discount_form.save()
                update_invoice_totals(invoice)
                messages.success(request, 'Réductions mises à jour!')
                return redirect('invoice-update', pk=invoice.id)
    
    form = InvoiceForm(instance=invoice)
    item_form = InvoiceItemForm()
    discount_form = InvoiceDiscountForm(instance=invoice)
    
    context = {
        'form': form,
        'item_form': item_form,
        'discount_form': discount_form,
        'invoice': invoice,
        'items': invoice.items.all(),
    }
    return render(request, 'invoice_app/invoice_edit.html', context)


def invoice_delete_item(request, pk):
    """Delete invoice item"""
    item = get_object_or_404(InvoiceItem, pk=pk)
    invoice = item.invoice
    item.delete()
    update_invoice_totals(invoice)
    messages.success(request, 'Article supprimé!')
    return redirect('invoice-update', pk=invoice.id)


def update_invoice_totals(invoice):
    """Recalculate invoice totals"""
    items = invoice.items.all()
    invoice.subtotal = sum(item.quantity * item.price for item in items)
    
    # Calculate total discount
    invoice.remise_amount = invoice.subtotal * (invoice.remise_percentage / Decimal('100'))
    invoice.rabais_amount = (invoice.subtotal - invoice.remise_amount) * (invoice.rabais_percentage / Decimal('100'))
    
    subtotal_after_discount = invoice.subtotal - invoice.remise_amount - invoice.rabais_amount
    
    invoice.escompte_amount = subtotal_after_discount * (invoice.escompte_percentage / Decimal('100'))
    invoice.total_discount = invoice.remise_amount + invoice.rabais_amount + invoice.escompte_amount
    
    final_subtotal = subtotal_after_discount - invoice.escompte_amount
    invoice.tva_amount = calculate_tva(final_subtotal, invoice.client.country)
    invoice.total = final_subtotal + invoice.tva_amount
    
    invoice.save()


class InvoiceDeleteView(DeleteView):
    model = Invoice
    template_name = 'invoice_app/invoice_confirm_delete.html'
    success_url = reverse_lazy('invoice-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Facture supprimée!')
        return super().delete(request, *args, **kwargs)


# ============== Payment Views ==============

def add_payment(request, invoice_id):
    """Add payment to invoice"""
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.save()
            
            invoice.amount_paid += payment.amount
            invoice.update_payment_status()
            invoice.save()
            
            messages.success(request, 'Paiement enregistré!')
            return redirect('invoice-detail', pk=invoice.id)
    else:
        form = PaymentForm()
        form.fields['amount'].initial = invoice.remaining_amount
    
    return render(request, 'invoice_app/payment_form.html', {'form': form, 'invoice': invoice})


# ============== Export Views ==============

def export_invoice_pdf(request, pk):
    """Export invoice as PDF"""
    invoice = get_object_or_404(Invoice, pk=pk)
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
    
    # Invoice title
    elements.append(Paragraph(f"<b>FACTURE {invoice.invoice_number}</b>", styles['Heading2']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Invoice info
    info_data = [
        ['Date:', invoice.date.strftime('%d/%m/%Y')],
        ['Échéance:', invoice.due_date.strftime('%d/%m/%Y')],
    ]
    info_table = Table(info_data, colWidths=[2*inch, 2*inch])
    elements.append(info_table)
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Client info
    elements.append(Paragraph("<b>Client:</b>", styles['Normal']))
    client_data = [
        [invoice.client.name],
        [invoice.client.delivery_address or ''],
        [f"{invoice.client.country}"],
    ]
    client_table = Table(client_data, colWidths=[3*inch])
    elements.append(client_table)
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Items table
    items_data = [['Description', 'Quantité', 'Prix U.', 'Total']]
    for item in invoice.items.all():
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
        ['Sous-total:', f"{invoice.subtotal:.2f}€"],
        ['Remise:', f"-{invoice.remise_amount:.2f}€"],
        ['Rabais:', f"-{invoice.rabais_amount:.2f}€"],
        ['Escompte:', f"-{invoice.escompte_amount:.2f}€"],
        ['TVA (20%):', f"{invoice.tva_amount:.2f}€"],
        ['<b>TOTAL TTC:</b>', f"<b>{invoice.total:.2f}€</b>"],
    ]
    totals_table = Table(totals_data, colWidths=[3*inch, 1.5*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(totals_table)
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Payment status
    elements.append(Paragraph(f"<b>Statut:</b> {invoice.get_payment_status_display()}", styles['Normal']))
    if invoice.payment_status != 'paid':
        elements.append(Paragraph(f"<b>Montant dû:</b> {invoice.remaining_amount:.2f}€", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
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
            invoice.client.name,
            invoice.date.strftime('%d/%m/%Y'),
            f"{invoice.subtotal:.2f}",
            f"{invoice.tva_amount:.2f}",
            f"{invoice.total:.2f}",
            invoice.get_payment_status_display(),
            f"{invoice.amount_paid:.2f}",
        ])
    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="Factures.xlsx"'
    wb.save(response)
    return response


# ============== Company Info Views ==============

def company_info_view(request):
    """View and update company information"""
    company_info, _ = CompanyInfo.objects.get_or_create(pk=1)
    
    if request.method == 'POST':
        form = CompanyInfoForm(request.POST, request.FILES, instance=company_info)
        if form.is_valid():
            form.save()
            messages.success(request, 'Informations entreprise mises à jour!')
            return redirect('company-info')
    else:
        form = CompanyInfoForm(instance=company_info)
    
    return render(request, 'invoice_app/company_info.html', {'form': form, 'company_info': company_info})


# ============== API Views ==============

def api_get_product_price(request, product_id):
    """API endpoint to get product price"""
    product = get_object_or_404(Product, pk=product_id)
    return JsonResponse({'price': float(product.price)})


def api_invoice_summary(request):
    """API endpoint to get invoice summary"""
    invoices = Invoice.objects.exclude(is_credit_note=True)
    total_invoices = invoices.count()
    total_revenue = invoices.aggregate(total=Sum('total'))['total'] or Decimal('0')
    paid = invoices.filter(payment_status='paid').count()
    pending = invoices.filter(payment_status='pending').count()
    
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
    quote.tva_amount = calculate_tva(final_subtotal, quote.client.country)
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
    quote = get_object_or_404(Quote, pk=pk)
    
    if quote.status == 'converted':
        messages.warning(request, 'Ce devis a déjà été converti en facture!')
        return redirect('quote-detail', pk=quote.id)
    
    # Create invoice from quote
    invoice = Invoice.objects.create(
        invoice_number=get_next_invoice_number(),
        client=quote.client,
        date=datetime.now(),
        due_date=datetime.now() + timedelta(days=30),
        subtotal=quote.subtotal,
        remise_percentage=quote.remise_percentage,
        remise_amount=quote.remise_amount,
        rabais_percentage=quote.rabais_percentage,
        rabais_amount=quote.rabais_amount,
        escompte_percentage=quote.escompte_percentage,
        escompte_amount=quote.escompte_amount,
        total_discount=quote.total_discount,
        tva_amount=quote.tva_amount,
        total=quote.total,
    )
    
    # Copy items from quote to invoice
    for quote_item in quote.items.all():
        InvoiceItem.objects.create(
            invoice=invoice,
            description=quote_item.description,
            quantity=quote_item.quantity,
            price=quote_item.price,
            product=quote_item.product,
        )
    
    # Update quote status
    quote.status = 'converted'
    quote.converted_invoice = invoice
    quote.save()
    
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
        [quote.client.name],
        [quote.client.delivery_address or ''],
        [f"{quote.client.country}"],
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
    template_name = 'invoice_app/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Notification.objects.select_related('client', 'invoice', 'quote')
        
        form = NotificationFilterForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('type'):
                queryset = queryset.filter(type=form.cleaned_data['type'])
            if form.cleaned_data.get('status'):
                queryset = queryset.filter(status=form.cleaned_data['status'])
            if form.cleaned_data.get('client'):
                queryset = queryset.filter(client=form.cleaned_data['client'])
            if form.cleaned_data.get('date_from'):
                queryset = queryset.filter(created_at__date__gte=form.cleaned_data['date_from'])
            if form.cleaned_data.get('date_to'):
                queryset = queryset.filter(created_at__date__lte=form.cleaned_data['date_to'])
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = NotificationFilterForm(self.request.GET)
        return context


def send_invoice_by_email(request, pk):
    """Send invoice to client by email"""
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
                messages.success(request, 'Email envoyé avec succès!')
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

class AuditLogListView(ListView):
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
