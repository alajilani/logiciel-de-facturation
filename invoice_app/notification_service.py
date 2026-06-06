from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from .models import Invoice, Notification


ALERT_TITLES = {
    "FACTURE_EN_RETARD": "Facture en retard",
    "STOCK_FAIBLE": "Stock faible",
    "RUPTURE_STOCK": "Rupture de stock",
    "PAIEMENT_PARTIEL": "Paiement partiel",
    "ECHEANCE_PROCHE": "Échéance proche",
}

ALERT_PRIORITIES = {
    "HAUTE": "HAUTE",
    "MOYENNE": "MOYENNE",
    "BASSE": "BASSE",
}

_LEGACY_TO_PRIORITY = {
    "ERROR": "HAUTE",
    "WARNING": "MOYENNE",
    "SUCCESS": "BASSE",
    "INFO": "BASSE",
}


def _format_amount(value):
    amount = Decimal(str(value or 0)).quantize(Decimal('0.01'))
    return f"{amount:.2f} €"


def _normalize_priority(level):
    normalized = (level or "").upper()
    if normalized in ALERT_PRIORITIES:
        return normalized
    return _LEGACY_TO_PRIORITY.get(normalized, ALERT_PRIORITIES["BASSE"])


def _is_actionable_alert(title):
    return title in ALERT_TITLES.values()


def create_business_notification(
    titre,
    message,
    type_notification,
    niveau='BASSE',
    lien='',
    client=None,
    invoice=None,
    quote=None,
    dedupe_window_minutes=30,
    force=False,
):
    """Create a business alert while avoiding short-window duplicates."""
    priority = _normalize_priority(niveau)

    # Keep the stream focused on actionable ERP alerts only.
    if not force and not _is_actionable_alert(titre):
        return None

    window_start = timezone.now() - timedelta(minutes=dedupe_window_minutes)
    duplicate_exists = Notification.objects.filter(
        titre=titre,
        message=message,
        type_notification=type_notification,
        niveau=priority,
        lien=lien or '',
        date_creation__gte=window_start,
    ).exists()

    if duplicate_exists:
        return None

    return Notification.objects.create(
        titre=titre,
        message=message,
        type_notification=type_notification,
        niveau=priority,
        lu=False,
        lien=lien or '',
        client=client,
        invoice=invoice,
        quote=quote,
    )


def notify_invoice_created(invoice):
    # Disabled by business rule: creation notifications are considered noise.
    return None


def notify_invoice_validated(invoice):
    # Disabled by business rule: validation notifications are considered noise.
    return None


def notify_invoice_cancelled(invoice):
    # Disabled by business rule: cancellation notifications are not part of key alerts.
    return None


def notify_invoice_overdue(invoice):
    due_date = invoice.due_date or timezone.now().date()
    days_overdue = max(1, (timezone.now().date() - due_date).days)
    return create_business_notification(
        titre=ALERT_TITLES["FACTURE_EN_RETARD"],
        message=(
            f"Facture : {invoice.invoice_number}\n"
            f"Client : {invoice.client.nom}\n"
            f"Retard : {days_overdue} jours\n"
            f"Reste a payer : {_format_amount(invoice.reste_a_payer)}"
        ),
        type_notification='FACTURE',
        niveau='HAUTE',
        lien=f"/invoices/{invoice.id}/",
        client=invoice.client,
        invoice=invoice,
        dedupe_window_minutes=720,
    )


def notify_payment_received(payment):
    projected_paid = Decimal(str(payment.invoice.amount_paid or 0)) + Decimal(str(payment.amount or 0))
    remaining = max(Decimal('0.00'), Decimal(str(payment.invoice.total_ttc or 0)) - projected_paid)

    # Complete payment alerts are intentionally disabled to reduce notification noise.
    if remaining == 0:
        return None

    return create_business_notification(
        titre=ALERT_TITLES["PAIEMENT_PARTIEL"],
        message=(
            f"Facture : {payment.invoice.invoice_number}\n"
            f"Client : {payment.invoice.client.nom}\n"
            f"Montant recu : {_format_amount(payment.amount)}\n"
            f"Reste a payer : {_format_amount(remaining)}"
        ),
        type_notification='PAIEMENT',
        niveau='MOYENNE',
        lien=f"/invoices/{payment.invoice.id}/",
        client=payment.invoice.client,
        invoice=payment.invoice,
        dedupe_window_minutes=60,
    )


def notify_due_date_soon(invoice, days_remaining):
    if days_remaining < 0 or float(invoice.reste_a_payer or 0) <= 0:
        return None

    return create_business_notification(
        titre=ALERT_TITLES["ECHEANCE_PROCHE"],
        message=(
            f"Facture : {invoice.invoice_number}\n"
            f"Client : {invoice.client.nom}\n"
            f"Echeance dans : {days_remaining} jour(s)\n"
            f"Reste a payer : {_format_amount(invoice.reste_a_payer)}"
        ),
        type_notification='FACTURE',
        niveau='MOYENNE',
        lien=f"/invoices/{invoice.id}/",
        client=invoice.client,
        invoice=invoice,
        dedupe_window_minutes=1440,
    )


def notify_stock_low(product):
    return create_business_notification(
        titre=ALERT_TITLES["STOCK_FAIBLE"],
        message=(
            f"Produit : {product.name}\n"
            f"Stock restant : {product.stock}"
        ),
        type_notification='STOCK',
        niveau='MOYENNE',
        lien=f"/products/{product.id}/",
        dedupe_window_minutes=240,
    )


def notify_stock_out(product):
    return create_business_notification(
        titre=ALERT_TITLES["RUPTURE_STOCK"],
        message=(
            f"Produit : {product.name}\n"
            "Stock restant : 0"
        ),
        type_notification='STOCK',
        niveau='HAUTE',
        lien=f"/products/{product.id}/",
        dedupe_window_minutes=240,
    )


def notify_client_created(client):
    # Disabled by business rule: client creation notifications are considered noise.
    return None


def refresh_due_soon_alerts(days_threshold=3, max_invoices=50):
    """Create due-soon alerts for unpaid invoices approaching due date."""
    today = timezone.now().date()
    max_due_date = today + timedelta(days=days_threshold)
    invoices = Invoice.objects.select_related('client').filter(
        due_date__gte=today,
        due_date__lte=max_due_date,
    ).exclude(statut__in=['PAYEE', 'ANNULEE']).order_by('due_date')[:max_invoices]

    for invoice in invoices:
        if float(invoice.reste_a_payer or 0) <= 0:
            continue
        days_remaining = (invoice.due_date - today).days
        notify_due_date_soon(invoice, days_remaining)
