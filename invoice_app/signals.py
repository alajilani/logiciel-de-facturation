"""
Django signals for automatic audit logging
"""
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import Client, Product, Invoice, InvoiceItem, Payment, Quote, QuoteItem, CompanyInfo, Notification, AuditLog
from .audit_utils import log_create, log_update, log_delete
from .middleware import get_current_request, get_current_user
from .notification_service import (
    notify_due_date_soon,
    notify_invoice_overdue,
    notify_payment_received,
    notify_stock_low,
    notify_stock_out,
)
from django.utils import timezone

# Store original values before changes
_object_cache = {}


def _get_object_cache_key(sender, obj_id):
    """Generate cache key for object"""
    return f"{sender.__name__}_{obj_id}"


def _cache_object_before_change(sender, instance):
    """Generic function to cache all object fields before changes"""
    if instance.pk:
        cached_data = {}
        # Cache all non-relation, non-internal fields
        for field in instance._meta.get_fields():
            # Skip relations and internal fields
            if field.many_to_one or field.many_to_many or field.one_to_many:
                continue
            if field.name in ['id', 'created_at', 'updated_at', 'created_on', 'updated_on']:
                continue
            try:
                value = getattr(instance, field.name)
                cached_data[field.name] = value
            except:
                pass
        
        if cached_data:
            _object_cache[_get_object_cache_key(sender, instance.pk)] = cached_data


def _log_object_change(sender, instance, created, request, user):
    """Generic function to log object changes"""
    if created:
        log_create(sender.__name__, instance, request, user)
    else:
        old_values = _object_cache.get(_get_object_cache_key(sender, instance.pk))
        log_update(sender.__name__, instance, request, user, old_values)
        # Clean up cache
        cache_key = _get_object_cache_key(sender, instance.pk)
        if cache_key in _object_cache:
            del _object_cache[cache_key]


# ============== Pre-save signal handlers (cache before change) ==============

@receiver(pre_save, sender=Client)
def cache_client(sender, instance, **kwargs):
    _cache_object_before_change(sender, instance)

@receiver(pre_save, sender=Product)
def cache_product(sender, instance, **kwargs):
    _cache_object_before_change(sender, instance)

@receiver(pre_save, sender=Invoice)
def cache_invoice(sender, instance, **kwargs):
    _cache_object_before_change(sender, instance)

@receiver(pre_save, sender=InvoiceItem)
def cache_invoiceitem(sender, instance, **kwargs):
    _cache_object_before_change(sender, instance)

@receiver(pre_save, sender=Payment)
def cache_payment(sender, instance, **kwargs):
    _cache_object_before_change(sender, instance)

@receiver(pre_save, sender=Quote)
def cache_quote(sender, instance, **kwargs):
    _cache_object_before_change(sender, instance)

@receiver(pre_save, sender=QuoteItem)
def cache_quoteitem(sender, instance, **kwargs):
    _cache_object_before_change(sender, instance)

@receiver(pre_save, sender=CompanyInfo)
def cache_companyinfo(sender, instance, **kwargs):
    _cache_object_before_change(sender, instance)

@receiver(pre_save, sender=Notification)
def cache_notification(sender, instance, **kwargs):
    _cache_object_before_change(sender, instance)


# ============== Post-save signal handlers (log after change) ==============

@receiver(post_save, sender=Client)
def log_client(sender, instance, created, **kwargs):
    try:
        _log_object_change(sender, instance, created, get_current_request(), get_current_user())
    except Exception as e:
        print(f"Error logging Client: {e}")

@receiver(post_save, sender=Product)
def log_product(sender, instance, created, **kwargs):
    try:
        _log_object_change(sender, instance, created, get_current_request(), get_current_user())
    except Exception as e:
        print(f"Error logging Product: {e}")

@receiver(post_save, sender=Invoice)
def log_invoice(sender, instance, created, **kwargs):
    try:
        _log_object_change(sender, instance, created, get_current_request(), get_current_user())
    except Exception as e:
        print(f"Error logging Invoice: {e}")

@receiver(post_save, sender=InvoiceItem)
def log_invoiceitem(sender, instance, created, **kwargs):
    try:
        _log_object_change(sender, instance, created, get_current_request(), get_current_user())
    except Exception as e:
        print(f"Error logging InvoiceItem: {e}")

@receiver(post_save, sender=Payment)
def log_payment(sender, instance, created, **kwargs):
    try:
        _log_object_change(sender, instance, created, get_current_request(), get_current_user())
    except Exception as e:
        print(f"Error logging Payment: {e}")

@receiver(post_save, sender=Quote)
def log_quote(sender, instance, created, **kwargs):
    try:
        _log_object_change(sender, instance, created, get_current_request(), get_current_user())
    except Exception as e:
        print(f"Error logging Quote: {e}")

@receiver(post_save, sender=QuoteItem)
def log_quoteitem(sender, instance, created, **kwargs):
    try:
        _log_object_change(sender, instance, created, get_current_request(), get_current_user())
    except Exception as e:
        print(f"Error logging QuoteItem: {e}")

@receiver(post_save, sender=CompanyInfo)
def log_companyinfo(sender, instance, created, **kwargs):
    try:
        _log_object_change(sender, instance, created, get_current_request(), get_current_user())
    except Exception as e:
        print(f"Error logging CompanyInfo: {e}")

@receiver(post_save, sender=Notification)
def log_notification(sender, instance, created, **kwargs):
    try:
        _log_object_change(sender, instance, created, get_current_request(), get_current_user())
    except Exception as e:
        print(f"Error logging Notification: {e}")


# ============== Business Notification Signal Handlers ==============

@receiver(post_save, sender=Client)
def business_notify_client(sender, instance, created, **kwargs):
    # Client creation alerts are intentionally disabled to avoid noise.
    return


@receiver(post_save, sender=Invoice)
def business_notify_invoice(sender, instance, created, **kwargs):
    try:
        if instance.due_date and float(instance.reste_a_payer or 0) > 0:
            days_remaining = (instance.due_date - timezone.now().date()).days
            if 0 <= days_remaining <= 3:
                notify_due_date_soon(instance, days_remaining)

        if instance.due_date and instance.due_date < timezone.now().date() and float(instance.reste_a_payer or 0) > 0:
            notify_invoice_overdue(instance)
    except Exception as e:
        print(f"Error business notification Invoice: {e}")


@receiver(post_save, sender=Payment)
def business_notify_payment(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        notify_payment_received(instance)
    except Exception as e:
        print(f"Error business notification Payment: {e}")


@receiver(post_save, sender=Product)
def business_notify_stock(sender, instance, created, **kwargs):
    try:
        if instance.type_item != 'PRODUIT' or not instance.suivre_stock:
            return
        if instance.stock <= 0:
            notify_stock_out(instance)
        elif instance.stock <= instance.seuil_alerte:
            notify_stock_low(instance)
    except Exception as e:
        print(f"Error business notification Stock: {e}")


# ============== Post-delete signal handlers (log deletion) ==============

@receiver(post_delete, sender=Client)
def log_client_delete(sender, instance, **kwargs):
    try:
        log_delete('Client', instance.pk, str(instance), get_current_request(), get_current_user())
    except Exception as e:
        print(f"Error logging Client deletion: {e}")

@receiver(post_delete, sender=Product)
def log_product_delete(sender, instance, **kwargs):
    try:
        log_delete('Product', instance.pk, str(instance), get_current_request(), get_current_user())
    except Exception as e:
        print(f"Error logging Product deletion: {e}")

@receiver(post_delete, sender=Invoice)
def log_invoice_delete(sender, instance, **kwargs):
    try:
        log_delete('Invoice', instance.pk, str(instance), get_current_request(), get_current_user())
    except Exception as e:
        print(f"Error logging Invoice deletion: {e}")

@receiver(post_delete, sender=InvoiceItem)
def log_invoiceitem_delete(sender, instance, **kwargs):
    try:
        log_delete('InvoiceItem', instance.pk, str(instance), get_current_request(), get_current_user())
    except Exception as e:
        print(f"Error logging InvoiceItem deletion: {e}")

@receiver(post_delete, sender=Payment)
def log_payment_delete(sender, instance, **kwargs):
    try:
        log_delete('Payment', instance.pk, str(instance), get_current_request(), get_current_user())
    except Exception as e:
        print(f"Error logging Payment deletion: {e}")

@receiver(post_delete, sender=Quote)
def log_quote_delete(sender, instance, **kwargs):
    try:
        log_delete('Quote', instance.pk, str(instance), get_current_request(), get_current_user())
    except Exception as e:
        print(f"Error logging Quote deletion: {e}")

@receiver(post_delete, sender=QuoteItem)
def log_quoteitem_delete(sender, instance, **kwargs):
    try:
        log_delete('QuoteItem', instance.pk, str(instance), get_current_request(), get_current_user())
    except Exception as e:
        print(f"Error logging QuoteItem deletion: {e}")

@receiver(post_delete, sender=CompanyInfo)
def log_companyinfo_delete(sender, instance, **kwargs):
    try:
        log_delete('CompanyInfo', instance.pk, str(instance), get_current_request(), get_current_user())
    except Exception as e:
        print(f"Error logging CompanyInfo deletion: {e}")

@receiver(post_delete, sender=Notification)
def log_notification_delete(sender, instance, **kwargs):
    try:
        log_delete('Notification', instance.pk, str(instance), get_current_request(), get_current_user())
    except Exception as e:
        print(f"Error logging Notification deletion: {e}")
