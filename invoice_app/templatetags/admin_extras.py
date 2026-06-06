"""Template tags utilisés par le tableau de bord /admin/."""

from django import template
from django.contrib.auth.models import User
from django.db.models import F, Sum

from invoice_app.models import (
    AuditLog,
    Client,
    Invoice,
    Product,
    Quote,
)

register = template.Library()


@register.filter(name="add_class")
def add_class(field, css):
    """Ajoute une classe CSS au widget d'un champ de formulaire."""
    try:
        existing = field.field.widget.attrs.get("class", "")
        classes = (existing + " " + css).strip()
        return field.as_widget(attrs={**field.field.widget.attrs, "class": classes})
    except Exception:
        return field


@register.simple_tag
def admin_kpis():
    """Retourne les indicateurs clés affichés sur la home /admin/."""
    revenue = Invoice.objects.aggregate(s=Sum("amount_paid"))["s"] or 0

    low_stock = (
        Product.objects.filter(
            type_item="PRODUIT",
            suivre_stock=True,
            stock__lte=F("seuil_alerte"),
        ).count()
    )

    return {
        "total_users": User.objects.count(),
        "active_users": User.objects.filter(is_active=True).count(),
        "total_clients": Client.objects.count(),
        "active_clients": Client.objects.filter(statut="ACTIF").count(),
        "total_invoices": Invoice.objects.count(),
        "total_quotes": Quote.objects.count(),
        "total_revenue": revenue,
        "overdue_invoices": Invoice.objects.filter(statut="EN_RETARD").count(),
        "unpaid_invoices": Invoice.objects.exclude(statut__in=["PAYEE", "ANNULEE"]).count(),
        "low_stock": low_stock,
    }


@register.simple_tag
def admin_recent_audit(limit=8):
    return AuditLog.objects.order_by("-timestamp")[:limit]


@register.simple_tag
def admin_recent_invoices(limit=5):
    return (
        Invoice.objects.select_related("client").order_by("-created_at")[:limit]
    )
