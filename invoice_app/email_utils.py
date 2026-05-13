# Email and Notification utilities

from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from .models import Notification, EmailTemplate
from datetime import datetime

def send_email_with_attachment(subject, message, recipient_email, attachment=None, attachment_filename=None):
    """
    Send email with optional PDF attachment
    
    Args:
        subject: Email subject
        message: Email body (HTML)
        recipient_email: Recipient email address
        attachment: File-like object or bytes
        attachment_filename: Filename for attachment
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    try:
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )
        email.content_subtype = "html"
        
        if attachment and attachment_filename:
            email.attach(attachment_filename, attachment, "application/pdf")
        
        email.send()
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False


def create_notification(notification_type, client, subject, message, recipient_email, 
                       invoice=None, quote=None):
    """
    Create a notification record
    
    Args:
        notification_type: Type of notification (from TYPE_CHOICES)
        client: Client instance
        subject: Email subject
        message: Email body
        recipient_email: Recipient email
        invoice: Associated invoice (optional)
        quote: Associated quote (optional)
    
    Returns:
        Notification: Created notification instance
    """
    notification = Notification.objects.create(
        type=notification_type,
        client=client,
        subject=subject,
        message=message,
        recipient_email=recipient_email,
        invoice=invoice,
        quote=quote,
        status='pending'
    )
    return notification


def send_invoice_email(invoice, custom_message=""):
    """
    Send invoice to client by email
    
    Args:
        invoice: Invoice instance
        custom_message: Optional custom message
    
    Returns:
        bool: True if successful
    """
    if not invoice.client.email:
        return False
    
    # Get email template or create default
    try:
        template = EmailTemplate.objects.get(template_type='invoice_sent')
        subject = template.subject
        body_template = template.body
    except EmailTemplate.DoesNotExist:
        subject = f"Facture {invoice.invoice_number}"
        body_template = """
        <h2>Facture {invoice_number}</h2>
        <p>Chère client,</p>
        <p>Veuillez trouver ci-joint votre facture N° {invoice_number} datée du {date}.</p>
        <p><strong>Montant TTC:</strong> {total}€</p>
        <p><strong>Date d'échéance:</strong> {due_date}</p>
        {custom_message}
        <p>Cordialement,</p>
        """
    
    # Format message
    body = body_template.format(
        invoice_number=invoice.invoice_number,
        date=invoice.date.strftime('%d/%m/%Y'),
        due_date=invoice.due_date.strftime('%d/%m/%Y'),
        total=f"{invoice.total:.2f}",
        custom_message=f"<p>{custom_message}</p>" if custom_message else ""
    )
    
    # Send email
    success = send_email_with_attachment(
        subject=subject,
        message=body,
        recipient_email=invoice.client.email,
    )
    
    # Create notification record
    notification = create_notification(
        notification_type='invoice_sent',
        client=invoice.client,
        subject=subject,
        message=body,
        recipient_email=invoice.client.email,
        invoice=invoice
    )
    
    if success:
        notification.status = 'sent'
        notification.sent_at = timezone.now()
    else:
        notification.status = 'failed'
        notification.error_message = 'Failed to send email'
    
    notification.save()
    return success


def send_quote_email(quote, custom_message=""):
    """
    Send quote to client by email
    
    Args:
        quote: Quote instance
        custom_message: Optional custom message
    
    Returns:
        bool: True if successful
    """
    if not quote.client.email:
        return False
    
    # Get email template or create default
    try:
        template = EmailTemplate.objects.get(template_type='quote_sent')
        subject = template.subject
        body_template = template.body
    except EmailTemplate.DoesNotExist:
        subject = f"Devis {quote.quote_number}"
        body_template = """
        <h2>Devis {quote_number}</h2>
        <p>Chère client,</p>
        <p>Veuillez trouver ci-joint notre devis N° {quote_number} datée du {date}.</p>
        <p><strong>Montant TTC:</strong> {total}€</p>
        <p><strong>Validité:</strong> jusqu'au {validity_date}</p>
        {custom_message}
        <p>N'hésitez pas à nous contacter pour toute question.</p>
        <p>Cordialement,</p>
        """
    
    # Format message
    body = body_template.format(
        quote_number=quote.quote_number,
        date=quote.date.strftime('%d/%m/%Y'),
        validity_date=quote.validity_date.strftime('%d/%m/%Y'),
        total=f"{quote.total:.2f}",
        custom_message=f"<p>{custom_message}</p>" if custom_message else ""
    )
    
    # Send email
    success = send_email_with_attachment(
        subject=subject,
        message=body,
        recipient_email=quote.client.email,
    )
    
    # Create notification record
    notification = create_notification(
        notification_type='quote_sent',
        client=quote.client,
        subject=subject,
        message=body,
        recipient_email=quote.client.email,
        quote=quote
    )
    
    if success:
        notification.status = 'sent'
        notification.sent_at = timezone.now()
    else:
        notification.status = 'failed'
        notification.error_message = 'Failed to send email'
    
    notification.save()
    return success


def send_payment_reminder(invoice):
    """
    Send payment reminder for overdue invoice
    
    Args:
        invoice: Invoice instance
    
    Returns:
        bool: True if successful
    """
    if not invoice.client.email:
        return False
    
    days_overdue = (timezone.now().date() - invoice.due_date).days
    
    subject = f"Rappel: Facture {invoice.invoice_number} impayée"
    body = f"""
    <h2>Rappel de paiement</h2>
    <p>Chère client,</p>
    <p>Notre facture N° {invoice.invoice_number} du {invoice.date.strftime('%d/%m/%Y')} 
    est restée impayée depuis {days_overdue} jours.</p>
    <p><strong>Montant à payer:</strong> {invoice.remaining_amount:.2f}€</p>
    <p>Veuillez effectuer le paiement dans les plus brefs délais.</p>
    <p>Cordialement,</p>
    """
    
    success = send_email_with_attachment(
        subject=subject,
        message=body,
        recipient_email=invoice.client.email,
    )
    
    # Create notification record
    create_notification(
        notification_type='invoice_overdue',
        client=invoice.client,
        subject=subject,
        message=body,
        recipient_email=invoice.client.email,
        invoice=invoice
    )
    
    return success


def send_payment_thank_you(invoice, payment_amount):
    """
    Send thank you email after payment
    
    Args:
        invoice: Invoice instance
        payment_amount: Amount paid
    
    Returns:
        bool: True if successful
    """
    if not invoice.client.email:
        return False
    
    remaining = invoice.remaining_amount
    status = "payée en intégralité" if remaining == 0 else f"partiellement payée (reste: {remaining:.2f}€)"
    
    subject = f"Confirmation de paiement - Facture {invoice.invoice_number}"
    body = f"""
    <h2>Confirmation de paiement</h2>
    <p>Chère client,</p>
    <p>Nous avons bien reçu votre paiement de {payment_amount:.2f}€.</p>
    <p>Votre facture N° {invoice.invoice_number} est maintenant {status}.</p>
    <p>Merci de votre confiance !</p>
    <p>Cordialement,</p>
    """
    
    success = send_email_with_attachment(
        subject=subject,
        message=body,
        recipient_email=invoice.client.email,
    )
    
    # Create notification record
    create_notification(
        notification_type='payment_received',
        client=invoice.client,
        subject=subject,
        message=body,
        recipient_email=invoice.client.email,
        invoice=invoice
    )
    
    return success


# ============================================================================
# TIER 4 - REAL-TIME NOTIFICATIONS
# ============================================================================

def create_realtime_notification(user, notification_type, title, message, priority='medium', 
                                  client=None, invoice=None, action_url=None):
    """
    Create a real-time notification for a user (Tier 4)
    
    Args:
        user: User instance
        notification_type: Type of notification (from NOTIFICATION_TYPES)
        title: Notification title
        message: Notification message
        priority: 'low', 'medium', 'high', 'critical'
        client: Associated client (optional)
        invoice: Associated invoice (optional)
        action_url: URL to redirect to when clicked (optional)
    
    Returns:
        RealtimeNotification: Created notification instance
    """
    from .models import RealtimeNotification
    
    notification = RealtimeNotification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        priority=priority,
        client=client,
        invoice=invoice,
        action_url=action_url,
        is_read=False,
        is_dismissed=False
    )
    return notification


def notify_invoice_created(user, invoice):
    """
    Notify when a new invoice is created (Tier 4)
    """
    create_realtime_notification(
        user=user,
        notification_type='new_invoice',
        title=f'Nouvelle facture créée: {invoice.invoice_number}',
        message=f'Facture {invoice.invoice_number} créée pour le client {invoice.client.name}',
        priority='medium',
        client=invoice.client,
        invoice=invoice,
        action_url=f'/invoices/{invoice.id}/'
    )


def notify_invoice_sent(user, invoice):
    """
    Notify when invoice is sent by email (Tier 4)
    """
    create_realtime_notification(
        user=user,
        notification_type='payment_reminder',
        title=f'Facture envoyée: {invoice.invoice_number}',
        message=f'Facture {invoice.invoice_number} envoyée au client {invoice.client.name} ({invoice.client.email})',
        priority='medium',
        client=invoice.client,
        invoice=invoice,
        action_url=f'/invoices/{invoice.id}/'
    )


def notify_payment_received(user, invoice, payment_amount):
    """
    Notify when payment is received (Tier 4)
    """
    create_realtime_notification(
        user=user,
        notification_type='payment_received',
        title=f'Paiement reçu: {payment_amount}€',
        message=f'Paiement de {payment_amount}€ reçu pour la facture {invoice.invoice_number}',
        priority='high',
        client=invoice.client,
        invoice=invoice,
        action_url=f'/invoices/{invoice.id}/'
    )


def notify_invoice_overdue(user, invoice):
    """
    Notify when invoice is overdue (Tier 4)
    """
    from datetime import datetime
    days_overdue = (datetime.now().date() - invoice.due_date).days
    
    create_realtime_notification(
        user=user,
        notification_type='invoice_overdue',
        title=f'⚠️ Facture en retard: {invoice.invoice_number}',
        message=f'Facture {invoice.invoice_number} en retard depuis {days_overdue} jours. Montant dû: {invoice.remaining_amount:.2f}€',
        priority='critical',
        client=invoice.client,
        invoice=invoice,
        action_url=f'/invoices/{invoice.id}/'
    )


def notify_quote_created(user, quote):
    """
    Notify when a new quote is created (Tier 4)
    """
    create_realtime_notification(
        user=user,
        notification_type='new_quote',
        title=f'Nouveau devis créé: {quote.quote_number}',
        message=f'Devis {quote.quote_number} créé pour le client {quote.client.name}',
        priority='medium',
        client=quote.client,
        action_url=f'/quotes/{quote.id}/'
    )


def notify_anomaly_detected(user, anomaly_type, title, message):
    """
    Notify when an anomaly is detected (Tier 3 → Tier 4)
    """
    create_realtime_notification(
        user=user,
        notification_type='anomaly_critical',
        title=f'🚨 Anomalie détectée: {title}',
        message=message,
        priority='critical'
    )

