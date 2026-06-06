# Email and Notification utilities

from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from .models import Notification, EmailTemplate
from .notification_service import create_business_notification
from datetime import datetime
import re


def _sanitize_internal_notification_text(text):
    """Remove client-facing phrases from dashboard notifications."""
    cleaned = strip_tags(text or '')
    # Remove common courtesy lines used in client emails.
    patterns = [
        r"ch[eè]re?\s+client[,\s]*",
        r"merci\s+de\s+votre\s+confiance\s*!?",
        r"cordialement[,\s]*",
        r"n['’]h[eé]sitez\s+pas\s+[aà]\s+nous\s+contacter[^.]*\.?",
        r"veuillez\s+trouver\s+ci-joint[^.]*\.?",
    ]
    for pattern in patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

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
    type_mapping = {
        'invoice_created': 'FACTURE',
        'invoice_sent': 'FACTURE',
        'invoice_paid': 'FACTURE',
        'invoice_overdue': 'FACTURE',
        'quote_created': 'SYSTEME',
        'quote_accepted': 'SYSTEME',
        'quote_rejected': 'SYSTEME',
        'payment_received': 'PAIEMENT',
        'reminder': 'SYSTEME',
    }
    level_mapping = {
        'invoice_overdue': 'WARNING',
        'payment_received': 'SUCCESS',
    }

    plain_message = _sanitize_internal_notification_text(message)

    notification = create_business_notification(
        titre=subject,
        message=plain_message,
        type_notification=type_mapping.get(notification_type, 'SYSTEME'),
        niveau=level_mapping.get(notification_type, 'INFO'),
        lien=f"/invoices/{invoice.id}/" if invoice else (f"/quotes/{quote.id}/" if quote else ''),
        client=client,
        invoice=invoice,
        quote=quote,
        dedupe_window_minutes=5,
    )

    if notification is None:
        # Keep compatibility for existing callsites expecting a Notification object.
        notification = Notification.objects.filter(
            titre=subject,
            type_notification=type_mapping.get(notification_type, 'SYSTEME'),
            client=client,
            invoice=invoice,
            quote=quote,
        ).order_by('-date_creation').first()

    if notification:
        notification.type = notification_type
        notification.subject = subject
        notification.recipient_email = recipient_email
        notification.status = notification.status or 'pending'
        notification.save(update_fields=['type', 'subject', 'recipient_email', 'status'])

    return notification


def send_invoice_email(invoice, custom_message="", send_attachment=True):
    """
    Send invoice to client by email (premium HTML + optional PDF attachment).

    Args:
        invoice: Invoice instance
        custom_message: Optional message from the accountant (shown in a dedicated block)
        send_attachment: When True, attach the generated invoice PDF

    Returns:
        bool: True if successful
    """
    from .models import CompanyInfo
    from .views import build_invoice_pdf_bytes

    if not invoice.client.email:
        return False

    company = CompanyInfo.objects.first()
    company_name = (company.name if company and company.name else 'Numa')

    # Build money formatter (FR)
    def _money(v):
        try:
            f = float(v or 0)
        except (TypeError, ValueError):
            f = 0.0
        s = f"{f:,.2f}".replace(',', ' ').replace('.', ',')
        return f"{s} €"

    # Status pill
    pill_map = {
        'BROUILLON':           ('#475569', '#f1f5f9', 'Brouillon'),
        'VALIDEE':             ('#4f46e5', '#eef0ff', 'Validée'),
        'ENVOYEE':             ('#b45309', '#fef3c7', 'Envoyée'),
        'PAYEE':               ('#15803d', '#dcfce7', 'Payée'),
        'PARTIELLEMENT_PAYEE': ('#0e7490', '#cffafe', 'Partiellement payée'),
        'EN_RETARD':           ('#b91c1c', '#fee2e2', 'En retard'),
        'ANNULEE':             ('#6b7280', '#f3f4f6', 'Annulée'),
    }
    pill_fg, pill_bg, pill_text = pill_map.get(
        invoice.statut, ('#4f46e5', '#eef0ff', invoice.get_statut_display())
    )

    client_name = (invoice.client.contact_principal or invoice.client.nom or '').strip()

    # Subject – with en-dash and company name
    subject = f"Facture {invoice.invoice_number} – {company_name}"

    context = {
        # Branding
        'company_name': company_name,
        'company_address': (company.address if company else ''),
        'company_phone': (company.phone if company else ''),
        'company_email': (company.email if company else ''),
        'company_website': (company.website if company else ''),
        'company_logo_url': '',  # Inline images via cid would require MIMEMultipart; left blank for safety
        'accent_color': '#6366f1',
        # Email chrome
        'email_title': 'Votre facture est disponible',
        'intro_line': "Nous vous remercions pour votre confiance. Votre facture est disponible et jointe à cet email au format PDF.",
        'closing_line': "Pour toute question concernant cette facture, nous restons à votre disposition.",
        'pill_fg': pill_fg, 'pill_bg': pill_bg, 'pill_text': pill_text,
        # Recipient
        'client_name': client_name,
        # Invoice recap
        'invoice_number': invoice.invoice_number,
        'invoice_date': invoice.date.strftime('%d/%m/%Y') if invoice.date else '',
        'invoice_due_date': invoice.due_date.strftime('%d/%m/%Y') if invoice.due_date else '',
        'invoice_payment_method': (invoice.get_payment_method_display()
                                   if getattr(invoice, 'payment_method', None) else ''),
        'invoice_total_ttc': _money(invoice.total_ttc),
        'invoice_public_url': '',  # No public portal yet → button hidden
        # Custom message (only rendered if truthy)
        'custom_message': (custom_message or '').strip(),
    }

    html_body = render_to_string('invoice_app/emails/invoice_sent.html', context)
    text_body = strip_tags(html_body)

    # Build the email
    success = False
    error_msg = ''
    try:
        email = EmailMessage(
            subject=subject,
            body=html_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[invoice.client.email],
        )
        email.content_subtype = 'html'

        # Attach PDF only when requested
        if send_attachment:
            try:
                pdf_bytes = build_invoice_pdf_bytes(invoice)
                filename = f"Facture_{invoice.invoice_number}.pdf"
                email.attach(filename, pdf_bytes, 'application/pdf')
            except Exception as exc:
                # We still send the email but log the issue
                error_msg = f"PDF generation failed: {exc}"
                print(f"[send_invoice_email] {error_msg}")

        email.send(fail_silently=False)
        success = True
    except Exception as exc:
        error_msg = str(exc)
        print(f"[send_invoice_email] Send error: {error_msg}")
        success = False

    # Notification record
    notification_message = (
        f"Facture {invoice.invoice_number} envoyée au client {invoice.client.nom}. "
        f"Montant: {_money(invoice.total_ttc)}."
    )
    notification = create_notification(
        notification_type='invoice_sent',
        client=invoice.client,
        subject=f"Facture envoyée: {invoice.invoice_number}",
        message=notification_message,
        recipient_email=invoice.client.email,
        invoice=invoice,
    )
    if notification is not None:
        if success:
            notification.status = 'sent'
            notification.sent_at = timezone.now()
        else:
            notification.status = 'failed'
            notification.error_message = error_msg or 'Failed to send email'
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
    
    notification_message = (
        f"Devis {quote.quote_number} envoyé au client {quote.client.nom}. "
        f"Montant: {quote.total:.2f} €."
    )

    # Create notification record
    notification = create_notification(
        notification_type='quote_sent',
        client=quote.client,
        subject=f"Devis envoyé: {quote.quote_number}",
        message=notification_message,
        recipient_email=quote.client.email,
        quote=quote
    )

    if notification is not None:
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
    <p><strong>Montant à payer:</strong> {invoice.reste_a_payer:.2f}€</p>
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
        subject=f"Facture en retard: {invoice.invoice_number}",
        message=f"La facture {invoice.invoice_number} a dépassé sa date d'échéance.",
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
    
    remaining = invoice.reste_a_payer
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
    
    # Internal payment notifications are produced only by payment signal handlers
    # to guarantee one business notification per payment event.
    
    return success


def send_payment_confirmation(payment):
    """
    Send a professional HTML payment confirmation email to the client.

    Distinguishes between partial and complete payment.
    Prevents sending the same email twice via payment.email_sent flag.
    Does not raise — logs any failure so the payment record is never blocked.

    Args:
        payment: Payment instance (must already be saved with invoice relationship)

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    invoice = payment.invoice
    client = invoice.client

    # Guard: no email address
    if not client.email:
        return False

    # Guard: already sent for this payment
    if payment.email_sent:
        return False

    # Resolve company info for branding
    from .models import CompanyInfo
    company = CompanyInfo.objects.first()

    company_logo_url = ''
    if company and company.logo:
        try:
            company_logo_url = company.logo.url
        except Exception:
            company_logo_url = ''

    # Resolve payment method display label
    methode_paiement = payment.get_payment_method_display() if payment.payment_method else '—'

    is_partial = invoice.reste_a_payer > 0

    # Common context
    ctx = {
        'invoice_number': invoice.invoice_number,
        'client_name': client.nom,
        'montant_paye': f"{payment.amount:.2f}",
        'total_ttc': f"{invoice.total_ttc:.2f}",
        'amount_paid_total': f"{invoice.amount_paid:.2f}",
        'reste_a_payer': f"{invoice.reste_a_payer:.2f}",
        'methode_paiement': methode_paiement,
        'date_paiement': payment.payment_date.strftime('%d/%m/%Y'),
        'reference': payment.reference or '',
        'company_name': company.name if company else '',
        'company_address': company.address if company else '',
        'company_phone': company.phone if company else '',
        'company_email': company.email if company else '',
        'company_website': (company.website if company and getattr(company, 'website', None) else ''),
        'company_logo_url': company_logo_url,
        # Email-chrome variables (base template)
        'email_title': 'Paiement reçu' if is_partial else 'Facture réglée',
        'intro_line': (
            "Nous confirmons la réception de votre paiement concernant la facture ci-dessous."
            if is_partial else
            f"Nous vous confirmons la bonne réception de votre règlement. La facture {invoice.invoice_number} est désormais intégralement réglée."
        ),
        'closing_line': (
            "Pour toute question concernant cette facture, n'hésitez pas à nous contacter."
            if is_partial else
            "Nous restons à votre disposition pour tout besoin futur."
        ),
        'pill_text': 'Paiement reçu' if is_partial else 'Facture réglée',
        'pill_bg': '#dbeafe' if is_partial else '#d1fae5',
        'pill_fg': '#1d4ed8' if is_partial else '#047857',
        'accent_color': '#2563eb' if is_partial else '#10b981',
    }

    if is_partial:
        subject = f"Paiement reçu – Facture {invoice.invoice_number}"
        template_name = 'invoice_app/emails/email_paiement_partiel.html'
    else:
        subject = f"Facture réglée – {invoice.invoice_number}"
        template_name = 'invoice_app/emails/email_paiement_complet.html'

    try:
        html_body = render_to_string(template_name, ctx)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(
            "send_payment_confirmation: template render failed for payment %s: %s",
            payment.pk, e
        )
        return False

    try:
        success = send_email_with_attachment(
            subject=subject,
            message=html_body,
            recipient_email=client.email,
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(
            "send_payment_confirmation: email send failed for payment %s: %s",
            payment.pk, e
        )
        return False

    if success:
        payment.email_sent = True
        payment.save(update_fields=['email_sent'])

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
    try:
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
    except Exception:
        # RealtimeNotification model not available
        return None


def notify_invoice_created(user, invoice):
    """
    Notify when a new invoice is created (Tier 4)
    """
    create_realtime_notification(
        user=user,
        notification_type='new_invoice',
        title=f'Nouvelle facture créée: {invoice.invoice_number}',
        message=f'Facture {invoice.invoice_number} créée pour le client {invoice.client.nom}',
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
        message=f'Facture {invoice.invoice_number} envoyée au client {invoice.client.nom} ({invoice.client.email})',
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
        message=f'Facture {invoice.invoice_number} en retard depuis {days_overdue} jours. Montant dû: {invoice.reste_a_payer:.2f}€',
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
        message=f'Devis {quote.quote_number} créé pour le client {quote.client.nom}',
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

