# ============================================================================
# TIER 3 - BONUS MASTER 🔥: Vues pour IA/Intelligence & Synchronisation
# ============================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models import Sum, Avg, Count
from datetime import datetime
import csv
from decimal import Decimal
from .models import (
    AnomalyDetection, RevenueForecast, IntelligentAlert, 
    AccountingSynchronization, Invoice, Client, Payment, Product, AuditLog
)
from .forms import (
    AnomalyFilterForm, IntelligentAlertFilterForm, RevenueForecastForm,
    AccountingSynchronizationForm, AnomalyResolutionForm, IntelligentAlertAcknowledgeForm
)


# Utility for logging
def log_action(request, action, model, obj_id, desc):
    try:
        AuditLog.objects.create(
            action=action,
            model=model,
            object_id=obj_id,
            object_str=desc,
            user=request.user.username if request else 'System',
            ip_address=request.META.get('REMOTE_ADDR', '') if request else '0.0.0.0'
        )
    except:
        pass


# ============================================================================
# ANOMALY DETECTION - Détection des anomalies
# ============================================================================

@login_required
def anomaly_list(request):
    """Liste des anomalies détectées par l'IA"""
    anomalies = AnomalyDetection.objects.all().order_by('-detected_at')
    
    form = AnomalyFilterForm(request.GET or None)
    if form.is_valid():
        if form.cleaned_data.get('anomaly_type'):
            anomalies = anomalies.filter(anomaly_type=form.cleaned_data['anomaly_type'])
        if form.cleaned_data.get('severity'):
            anomalies = anomalies.filter(severity=form.cleaned_data['severity'])
        if form.cleaned_data.get('is_resolved') is not None:
            anomalies = anomalies.filter(is_resolved=form.cleaned_data['is_resolved'])
        if form.cleaned_data.get('date_from'):
            anomalies = anomalies.filter(detected_at__gte=form.cleaned_data['date_from'])
        if form.cleaned_data.get('date_to'):
            anomalies = anomalies.filter(detected_at__lte=form.cleaned_data['date_to'])
    
    paginator = Paginator(anomalies, 20)
    page_number = request.GET.get('page')
    anomalies = paginator.get_page(page_number)
    
    total = AnomalyDetection.objects.count()
    unresolved = AnomalyDetection.objects.filter(is_resolved=False).count()
    critical = AnomalyDetection.objects.filter(severity='critical').count()
    
    log_action(request, 'view', 'AnomalyDetection', 0, 'Consulté liste anomalies')
    
    context = {
        'anomalies': anomalies,
        'form': form,
        'total': total,
        'unresolved': unresolved,
        'critical': critical,
    }
    return render(request, 'invoice_app/anomaly_list.html', context)


@login_required
def anomaly_detail(request, pk):
    """Détail d'une anomalie et résolution"""
    anomaly = get_object_or_404(AnomalyDetection, pk=pk)
    
    if request.method == 'POST':
        form = AnomalyResolutionForm(request.POST, instance=anomaly)
        if form.is_valid():
            if form.cleaned_data['is_resolved']:
                anomaly.resolved_at = datetime.now()
            else:
                anomaly.resolved_at = None
            
            form.save()
            log_action(request, 'update', 'AnomalyDetection', anomaly.id, f"Anomalie résolu")
            messages.success(request, "Anomalie mise à jour avec succès!")
            return redirect('anomaly_detail', pk=pk)
    else:
        form = AnomalyResolutionForm(instance=anomaly)
    
    log_action(request, 'view', 'AnomalyDetection', anomaly.id, f"Consulté anomalie")
    
    context = {'anomaly': anomaly, 'form': form}
    return render(request, 'invoice_app/anomaly_detail.html', context)


# ============================================================================
# REVENUE FORECAST - Prévisions de CA
# ============================================================================

@login_required
def forecast_dashboard(request):
    """Dashboard des prévisions de CA"""
    forecasts = RevenueForecast.objects.all().order_by('-forecast_date')
    latest_forecast = forecasts.first()
    avg_accuracy = RevenueForecast.objects.filter(accuracy__isnull=False).aggregate(Avg('accuracy'))['accuracy__avg'] or 0
    monthly_forecasts = RevenueForecast.objects.filter(period='monthly').order_by('forecast_date')[:12]
    
    log_action(request, 'view', 'RevenueForecast', 0, 'Consulté dashboard prévisions')
    
    context = {
        'latest_forecast': latest_forecast,
        'forecasts': forecasts[:10],
        'avg_accuracy': avg_accuracy,
        'monthly_forecasts': monthly_forecasts,
    }
    return render(request, 'invoice_app/forecast_dashboard.html', context)


@login_required
def forecast_create(request):
    """Créer une nouvelle prévision"""
    if request.method == 'POST':
        form = RevenueForecastForm(request.POST)
        if form.is_valid():
            forecast = form.save(commit=False)
            forecast.confidence_interval_low = forecast.predicted_revenue * Decimal('0.85')
            forecast.confidence_interval_high = forecast.predicted_revenue * Decimal('1.15')
            forecast.save()
            
            log_action(request, 'create', 'RevenueForecast', forecast.id, f"Créé prévision")
            messages.success(request, "Prévision créée avec succès!")
            return redirect('forecast_dashboard')
    else:
        form = RevenueForecastForm()
    
    return render(request, 'invoice_app/forecast_form.html', {'form': form})


# ============================================================================
# INTELLIGENT ALERTS - Alertes intelligentes
# ============================================================================

@login_required
def alert_list(request):
    """Liste des alertes intelligentes"""
    alerts = IntelligentAlert.objects.all().order_by('-created_at')
    
    form = IntelligentAlertFilterForm(request.GET or None)
    if form.is_valid():
        if form.cleaned_data.get('alert_type'):
            alerts = alerts.filter(alert_type=form.cleaned_data['alert_type'])
        if form.cleaned_data.get('priority'):
            alerts = alerts.filter(priority=form.cleaned_data['priority'])
        if form.cleaned_data.get('is_acknowledged') is not None:
            alerts = alerts.filter(is_acknowledged=form.cleaned_data['is_acknowledged'])
    
    paginator = Paginator(alerts, 20)
    page_number = request.GET.get('page')
    alerts = paginator.get_page(page_number)
    
    total = IntelligentAlert.objects.count()
    unacknowledged = IntelligentAlert.objects.filter(is_acknowledged=False).count()
    urgent = IntelligentAlert.objects.filter(priority='urgent').count()
    
    log_action(request, 'view', 'IntelligentAlert', 0, 'Consulté liste alertes')
    
    context = {
        'alerts': alerts,
        'form': form,
        'total': total,
        'unacknowledged': unacknowledged,
        'urgent': urgent,
    }
    return render(request, 'invoice_app/alert_list.html', context)


@login_required
def alert_acknowledge(request, pk):
    """Confirmer/reconnaître une alerte"""
    alert = get_object_or_404(IntelligentAlert, pk=pk)
    
    if request.method == 'POST':
        alert.is_acknowledged = True
        alert.acknowledged_by = request.user.username
        alert.acknowledged_at = datetime.now()
        alert.save()
        
        log_action(request, 'update', 'IntelligentAlert', alert.id, f"Alerte confirmée")
        messages.success(request, "Alerte confirmée!")
        return redirect('alert_list')
    
    return render(request, 'invoice_app/alert_acknowledge.html', {'alert': alert})


# ============================================================================
# ACCOUNTING SYNCHRONIZATION - Export CSV & Synchronisation
# ============================================================================

@login_required
def accounting_export_form(request):
    """Formulaire pour export comptable"""
    if request.method == 'POST':
        form = AccountingSynchronizationForm(request.POST)
        if form.is_valid():
            sync = AccountingSynchronization(
                export_type=form.cleaned_data['export_type'],
                status='processing',
                start_date=form.cleaned_data['start_date'],
                end_date=form.cleaned_data['end_date'],
                created_by=request.user.username,
            )
            sync.save()
            
            export_format = form.cleaned_data['format']
            
            try:
                export_type = form.cleaned_data['export_type']
                if export_type == 'invoices':
                    return export_invoices_csv(sync, form.cleaned_data['start_date'], form.cleaned_data['end_date'])
                elif export_type == 'payments':
                    return export_payments_csv(sync, form.cleaned_data['start_date'], form.cleaned_data['end_date'])
                elif export_type == 'clients':
                    return export_clients_csv(sync)
                elif export_type == 'products':
                    return export_products_csv(sync)
                elif export_type == 'journal':
                    return export_journal_csv(sync, form.cleaned_data['start_date'], form.cleaned_data['end_date'])
                else:
                    return export_trial_balance_csv(sync, form.cleaned_data['end_date'])
                    
            except Exception as e:
                sync.status = 'failed'
                sync.error_message = str(e)
                sync.save()
                messages.error(request, f"Erreur lors de l'export: {str(e)}")
                return redirect('accounting_export_form')
    else:
        form = AccountingSynchronizationForm()
    
    return render(request, 'invoice_app/accounting_export_form.html', {'form': form})


def export_invoices_csv(sync, start_date, end_date):
    """Exporter les factures en CSV"""
    invoices = Invoice.objects.filter(date__range=[start_date, end_date]).order_by('date')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="export_factures.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Numéro', 'Client', 'Date', 'Montant HT', 'TVA', 'Total', 'Statut'])
    
    for invoice in invoices:
        writer.writerow([
            invoice.invoice_number,
            invoice.client.name,
            invoice.date.strftime('%Y-%m-%d'),
            str(invoice.subtotal or 0),
            str(invoice.tva_amount or 0),
            str(invoice.total or 0),
            invoice.get_payment_status_display(),
        ])
    
    sync.status = 'completed'
    sync.records_count = invoices.count()
    sync.completed_at = datetime.now()
    sync.file_path = f"export_factures_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    sync.save()
    
    return response


def export_payments_csv(sync, start_date, end_date):
    """Exporter les paiements en CSV"""
    payments = Payment.objects.filter(payment_date__range=[start_date, end_date]).order_by('payment_date')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="export_paiements.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Facture', 'Client', 'Date Paiement', 'Montant', 'Méthode'])
    
    for payment in payments:
        writer.writerow([
            payment.invoice.invoice_number,
            payment.invoice.client.name,
            payment.payment_date.strftime('%Y-%m-%d'),
            str(payment.amount),
            payment.get_payment_method_display(),
        ])
    
    sync.status = 'completed'
    sync.records_count = payments.count()
    sync.completed_at = datetime.now()
    sync.file_path = f"export_paiements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    sync.save()
    
    return response


def export_clients_csv(sync):
    """Exporter les clients en CSV"""
    clients = Client.objects.all().order_by('name')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="export_clients.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Nom', 'Email', 'Téléphone', 'Pays', 'Adresse', 'TVA'])
    
    for client in clients:
        writer.writerow([
            client.name,
            client.email or '',
            client.phone or '',
            client.country,
            client.delivery_address or '',
            client.tva_intra or '',
        ])
    
    sync.status = 'completed'
    sync.records_count = clients.count()
    sync.completed_at = datetime.now()
    sync.file_path = f"export_clients_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    sync.save()
    
    return response


def export_products_csv(sync):
    """Exporter les produits en CSV"""
    products = Product.objects.all().order_by('name')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="export_produits.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Nom', 'Référence', 'Prix', 'Description'])
    
    for product in products:
        writer.writerow([
            product.name,
            product.reference,
            str(product.price),
            product.description or '',
        ])
    
    sync.status = 'completed'
    sync.records_count = products.count()
    sync.completed_at = datetime.now()
    sync.file_path = f"export_produits_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    sync.save()
    
    return response


def export_journal_csv(sync, start_date, end_date):
    """Exporter journal comptable"""
    invoices = Invoice.objects.filter(date__range=[start_date, end_date]).order_by('date')
    payments = Payment.objects.filter(payment_date__range=[start_date, end_date]).order_by('payment_date')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="export_journal.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Type', 'Numéro', 'Description', 'Débit', 'Crédit', 'Solde'])
    
    total = Decimal('0')
    for invoice in invoices:
        writer.writerow([
            invoice.date.strftime('%Y-%m-%d'),
            'Facture',
            invoice.invoice_number,
            f"Facture {invoice.client.name}",
            str(invoice.total or 0),
            '',
            str(total + (invoice.total or 0)),
        ])
        total += invoice.total or 0
    
    for payment in payments:
        writer.writerow([
            payment.payment_date.strftime('%Y-%m-%d'),
            'Paiement',
            payment.invoice.invoice_number,
            f"Paiement {payment.invoice.client.name}",
            '',
            str(payment.amount),
            str(total - payment.amount),
        ])
        total -= payment.amount
    
    sync.status = 'completed'
    sync.records_count = invoices.count() + payments.count()
    sync.completed_at = datetime.now()
    sync.file_path = f"export_journal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    sync.save()
    
    return response


def export_trial_balance_csv(sync, end_date):
    """Exporter balance trial"""
    invoices = Invoice.objects.filter(date__lte=end_date)
    payments = Payment.objects.filter(payment_date__lte=end_date)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="export_balance.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Compte', 'Débit', 'Crédit', 'Solde'])
    
    total_invoices = invoices.aggregate(Sum('total'))['total__sum'] or Decimal('0')
    total_payments = payments.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    
    writer.writerow(['Comptes clients', str(total_invoices), '', str(total_invoices)])
    writer.writerow(['Paiements reçus', '', str(total_payments), str(total_invoices - total_payments)])
    writer.writerow(['TOTAL', str(total_invoices), str(total_payments), str(total_invoices - total_payments)])
    
    sync.status = 'completed'
    sync.records_count = invoices.count() + payments.count()
    sync.completed_at = datetime.now()
    sync.file_path = f"export_balance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    sync.save()
    
    return response


@login_required
def synchronization_history(request):
    """Historique des synchronisations"""
    syncs = AccountingSynchronization.objects.all().order_by('-created_at')
    
    paginator = Paginator(syncs, 20)
    page_number = request.GET.get('page')
    syncs = paginator.get_page(page_number)
    
    total = AccountingSynchronization.objects.count()
    completed = AccountingSynchronization.objects.filter(status='completed').count()
    failed = AccountingSynchronization.objects.filter(status='failed').count()
    
    log_action(request, 'view', 'AccountingSynchronization', 0, 'Consulté historique')
    
    context = {
        'syncs': syncs,
        'total': total,
        'completed': completed,
        'failed': failed,
    }
    return render(request, 'invoice_app/synchronization_history.html', context)


@login_required
def ia_dashboard(request):
    """Dashboard principal Tier 3: IA & Intelligence"""
    
    total_anomalies = AnomalyDetection.objects.count()
    unresolved_anomalies = AnomalyDetection.objects.filter(is_resolved=False).count()
    critical_anomalies = AnomalyDetection.objects.filter(severity='critical').count()
    high_confidence = AnomalyDetection.objects.filter(confidence__gte=80).count()
    
    total_alerts = IntelligentAlert.objects.count()
    unacknowledged_alerts = IntelligentAlert.objects.filter(is_acknowledged=False).count()
    urgent_alerts = IntelligentAlert.objects.filter(priority='urgent').count()
    
    latest_forecast = RevenueForecast.objects.first()
    
    recent_anomalies = AnomalyDetection.objects.all().order_by('-detected_at')[:5]
    recent_alerts = IntelligentAlert.objects.all().order_by('-created_at')[:5]
    
    log_action(request, 'view', 'Dashboard', 0, 'Consulté dashboard IA')
    
    context = {
        'total_anomalies': total_anomalies,
        'unresolved_anomalies': unresolved_anomalies,
        'critical_anomalies': critical_anomalies,
        'high_confidence': high_confidence,
        'total_alerts': total_alerts,
        'unacknowledged_alerts': unacknowledged_alerts,
        'urgent_alerts': urgent_alerts,
        'latest_forecast': latest_forecast,
        'recent_anomalies': recent_anomalies,
        'recent_alerts': recent_alerts,
    }
    return render(request, 'invoice_app/ia_dashboard.html', context)
