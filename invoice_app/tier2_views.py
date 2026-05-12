"""
Tier 2 Views: Multi-Currency, Advanced Search, Invoice Archiving
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q
from datetime import datetime
from decimal import Decimal

from .models import Invoice, Quote, Client, SearchIndex, ArchiveLog, ExchangeRate
from .forms import ArchiveForm, UnarchiveForm, AdvancedSearchForm, ExchangeRateForm
from .audit_utils import log_action


# ============== Multi-Currency Views ==============

@login_required
def exchange_rates_list(request):
    """List all exchange rates with ability to add new ones"""
    rates = ExchangeRate.objects.all().order_by('-date')
    
    if request.method == 'POST':
        form = ExchangeRateForm(request.POST)
        if form.is_valid():
            ExchangeRate.objects.create(
                from_currency=form.cleaned_data['from_currency'],
                to_currency=form.cleaned_data['to_currency'],
                rate=form.cleaned_data['rate'],
                date=datetime.now().date()
            )
            return redirect('exchange_rates_list')
    else:
        form = ExchangeRateForm()
    
    context = {
        'rates': rates,
        'form': form,
        'active_page': 'exchange_rates',
    }
    return render(request, 'invoice_app/exchange_rates_list.html', context)


def convert_currency(from_currency, to_currency, amount, date=None):
    """Convert amount from one currency to another using latest exchange rate"""
    if from_currency == to_currency:
        return amount
    
    if date is None:
        date = datetime.now().date()
    
    # Try to find exact rate
    rate_obj = ExchangeRate.objects.filter(
        from_currency=from_currency,
        to_currency=to_currency,
        date__lte=date
    ).order_by('-date').first()
    
    if rate_obj:
        return amount * rate_obj.rate
    
    # If not found, try reverse conversion
    rate_obj = ExchangeRate.objects.filter(
        from_currency=to_currency,
        to_currency=from_currency,
        date__lte=date
    ).order_by('-date').first()
    
    if rate_obj:
        return amount / rate_obj.rate
    
    # Return original amount if no rate found
    return amount


@login_required
def invoice_convert_currency(request, invoice_id):
    """Convert invoice to different currency"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if request.method == 'POST':
        new_currency = request.POST.get('currency')
        if new_currency and new_currency != invoice.currency:
            # Calculate new totals in target currency
            exchange_rate = convert_currency(invoice.currency, new_currency, Decimal('1.0'))
            
            # Update invoice
            invoice.original_currency = invoice.currency
            invoice.currency = new_currency
            invoice.exchange_rate = exchange_rate
            invoice.save()
            
            # Log action
            log_action('update', 'Invoice', invoice, request, None)
            
            return redirect('invoice_detail', id=invoice_id)
    
    currencies = ['EUR', 'USD', 'GBP']
    context = {
        'invoice': invoice,
        'currencies': [c for c in currencies if c != invoice.currency],
    }
    return render(request, 'invoice_app/invoice_convert_currency.html', context)


# ============== Advanced Search Views ==============

def update_search_index(content_type, obj):
    """Update search index for an object"""
    if content_type == 'invoice':
        SearchIndex.objects.filter(content_type='invoice', object_id=obj.id).delete()
        SearchIndex.objects.create(
            content_type='invoice',
            object_id=obj.id,
            search_text=f"{obj.invoice_number} {obj.client.name}",
            keywords=f"{obj.invoice_number} facture invoice {obj.client.name}",
            document_number=obj.invoice_number,
            client_name=obj.client.name,
            amount=obj.total,
            date=obj.date,
        )
    elif content_type == 'quote':
        SearchIndex.objects.filter(content_type='quote', object_id=obj.id).delete()
        SearchIndex.objects.create(
            content_type='quote',
            object_id=obj.id,
            search_text=f"{obj.quote_number} {obj.client.name}",
            keywords=f"{obj.quote_number} devis quote {obj.client.name}",
            document_number=obj.quote_number,
            client_name=obj.client.name,
            amount=obj.total,
            date=obj.date,
        )
    elif content_type == 'client':
        SearchIndex.objects.filter(content_type='client', object_id=obj.id).delete()
        SearchIndex.objects.create(
            content_type='client',
            object_id=obj.id,
            search_text=obj.name,
            keywords=f"{obj.name} client",
            client_name=obj.name,
        )


@login_required
def advanced_search(request):
    """Advanced search with filters"""
    form = AdvancedSearchForm()
    results = {
        'invoices': [],
        'quotes': [],
        'clients': [],
    }
    total_results = 0
    
    if request.method == 'POST' or request.GET.get('search_text'):
        form = AdvancedSearchForm(request.POST or request.GET)
        if form.is_valid():
            search_text = form.cleaned_data.get('search_text', '').lower()
            search_type = form.cleaned_data.get('search_type', 'all')
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            
            # Build query
            query = Q()
            if search_text:
                query = Q(search_text__icontains=search_text) | Q(keywords__icontains=search_text)
            
            # Filter by date
            if date_from and date_to:
                query &= Q(date__gte=date_from) & Q(date__lte=date_to)
            elif date_from:
                query &= Q(date__gte=date_from)
            elif date_to:
                query &= Q(date__lte=date_to)
            
            # Search by type
            if search_type in ['all', 'invoice']:
                invoices = SearchIndex.objects.filter(content_type='invoice').filter(query)
                for idx in invoices:
                    invoice = Invoice.objects.filter(id=idx.object_id).first()
                    if invoice:
                        results['invoices'].append(invoice)
            
            if search_type in ['all', 'quote']:
                quotes = SearchIndex.objects.filter(content_type='quote').filter(query)
                for idx in quotes:
                    quote = Quote.objects.filter(id=idx.object_id).first()
                    if quote:
                        results['quotes'].append(quote)
            
            if search_type in ['all', 'client']:
                clients = SearchIndex.objects.filter(content_type='client').filter(query)
                for idx in clients:
                    client = Client.objects.filter(id=idx.object_id).first()
                    if client:
                        results['clients'].append(client)
            
            total_results = len(results['invoices']) + len(results['quotes']) + len(results['clients'])
    
    context = {
        'form': form,
        'results': results,
        'total_results': total_results,
        'active_page': 'advanced_search',
    }
    return render(request, 'invoice_app/advanced_search.html', context)


# ============== Invoice Archiving Views ==============

@login_required
def invoice_archive(request, invoice_id):
    """Archive an invoice"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if request.method == 'POST':
        form = ArchiveForm(request.POST)
        if form.is_valid():
            # Mark as archived
            invoice.is_archived = True
            invoice.archived_at = datetime.now()
            invoice.archived_by = request.user.username
            invoice.save()
            
            # Create archive log
            ArchiveLog.objects.update_or_create(
                invoice=invoice,
                defaults={
                    'archived_by': request.user.username,
                    'archived_at': datetime.now(),
                    'reason': form.cleaned_data['reason'],
                }
            )
            
            # Log action
            log_action('update', 'Invoice', invoice, request, None)
            
            return redirect('invoice_list')
    else:
        form = ArchiveForm()
    
    context = {
        'invoice': invoice,
        'form': form,
    }
    return render(request, 'invoice_app/invoice_archive.html', context)


@login_required
def invoice_unarchive(request, invoice_id):
    """Unarchive an archived invoice"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if not invoice.is_archived:
        return HttpResponseForbidden("Cette facture n'est pas archivée")
    
    if request.method == 'POST':
        form = UnarchiveForm(request.POST)
        if form.is_valid():
            # Mark as unarchived
            invoice.is_archived = False
            invoice.save()
            
            # Update archive log
            archive_log = ArchiveLog.objects.filter(invoice=invoice).first()
            if archive_log:
                archive_log.unarchived_by = request.user.username
                archive_log.unarchived_at = datetime.now()
                archive_log.unarchive_reason = form.cleaned_data['reason']
                archive_log.save()
            
            # Log action
            log_action('update', 'Invoice', invoice, request, None)
            
            return redirect('invoice_detail', id=invoice_id)
    else:
        form = UnarchiveForm()
    
    archive_log = ArchiveLog.objects.filter(invoice=invoice).first()
    
    context = {
        'invoice': invoice,
        'form': form,
        'archive_log': archive_log,
    }
    return render(request, 'invoice_app/invoice_unarchive.html', context)


@login_required
def archived_invoices_list(request):
    """List all archived invoices"""
    invoices = Invoice.objects.filter(is_archived=True).order_by('-archived_at')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(invoices, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'invoices': page_obj.object_list,
        'active_page': 'archived_invoices',
    }
    return render(request, 'invoice_app/archived_invoices_list.html', context)


@login_required
def archive_logs_detail(request, invoice_id):
    """View archive history for an invoice"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    archive_log = ArchiveLog.objects.filter(invoice=invoice).first()
    
    context = {
        'invoice': invoice,
        'archive_log': archive_log,
    }
    return render(request, 'invoice_app/archive_logs_detail.html', context)
