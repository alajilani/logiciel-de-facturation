from django import forms
from .models import (
    Client, Product, Invoice, InvoiceItem, Payment, CompanyInfo, Quote, QuoteItem, 
    Notification, EmailTemplate, AnomalyDetection, RevenueForecast, IntelligentAlert,
    AccountingSynchronization
)
from django.conf import settings

class ClientForm(forms.ModelForm):
    country = forms.ChoiceField(choices=[(c, c) for c in settings.COUNTRIES])
    
    class Meta:
        model = Client
        fields = ['name', 'email', 'phone', 'delivery_address', 'billing_address', 'country', 'tva_intra']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du client'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Téléphone'}),
            'delivery_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Adresse de livraison'}),
            'billing_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Adresse de facturation'}),
            'country': forms.Select(attrs={'class': 'form-control'}),
            'tva_intra': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numéro TVA Intracommunautaire'}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'reference', 'description', 'stock_quantity', 'low_stock_threshold', 'track_stock']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du produit'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Prix', 'step': '0.01'}),
            'reference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Référence'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': 'Stock'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': 'Seuil d\'alerte'}),
            'track_stock': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CompanyInfoForm(forms.ModelForm):
    country = forms.ChoiceField(choices=[(c, c) for c in settings.COUNTRIES])
    
    class Meta:
        model = CompanyInfo
        fields = ['name', 'address', 'phone', 'email', 'website', 'siret', 'siren', 'tva_number', 'logo', 'country']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de l\'entreprise'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Adresse'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Téléphone'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Site web'}),
            'siret': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SIRET'}),
            'siren': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SIREN'}),
            'tva_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numéro TVA'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'country': forms.Select(attrs={'class': 'form-control'}),
        }


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['client', 'date', 'due_date', 'payment_method']
        widgets = {
            'client': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
        }


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['description', 'quantity', 'price', 'product']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Description'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Quantité', 'min': '1'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Prix', 'step': '0.01'}),
            'product': forms.Select(attrs={'class': 'form-control'}),
        }


class InvoiceDiscountForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['remise_percentage', 'remise_amount', 'rabais_percentage', 'rabais_amount', 
                  'escompte_percentage', 'escompte_amount']
        widgets = {
            'remise_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '%'}),
            'remise_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Montant'}),
            'rabais_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '%'}),
            'rabais_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Montant'}),
            'escompte_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '%'}),
            'escompte_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Montant'}),
        }


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_method', 'payment_date', 'reference', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Montant'}),
            'payment_method': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Méthode de paiement'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Référence'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notes'}),
        }


class InvoiceFilterForm(forms.Form):
    client = forms.ModelChoiceField(queryset=Client.objects.all(), required=False, 
                                   widget=forms.Select(attrs={'class': 'form-control'}),
                                   label="Client")
    payment_status = forms.ChoiceField(choices=[('', '-- Tous les statuts --')] + Invoice.PAYMENT_STATUS_CHOICES,
                                      required=False, widget=forms.Select(attrs={'class': 'form-control'}),
                                      label="Statut de paiement")
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
                               label="Du")
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
                             label="Au")


class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ['client', 'date', 'validity_date', 'terms_conditions', 'notes']
        widgets = {
            'client': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'validity_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'terms_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Conditions générales'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notes'}),
        }


class QuoteItemForm(forms.ModelForm):
    class Meta:
        model = QuoteItem
        fields = ['description', 'quantity', 'price', 'product']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Description'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Quantité', 'min': '1'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Prix', 'step': '0.01'}),
            'product': forms.Select(attrs={'class': 'form-control'}),
        }


class QuoteDiscountForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ['remise_percentage', 'remise_amount', 'rabais_percentage', 'rabais_amount', 
                  'escompte_percentage', 'escompte_amount']
        widgets = {
            'remise_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '%'}),
            'remise_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Montant'}),
            'rabais_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '%'}),
            'rabais_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Montant'}),
            'escompte_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '%'}),
            'escompte_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Montant'}),
        }


class QuoteFilterForm(forms.Form):
    client = forms.ModelChoiceField(queryset=Client.objects.all(), required=False, 
                                   widget=forms.Select(attrs={'class': 'form-control'}),
                                   label="Client")
    status = forms.ChoiceField(choices=[('', '-- Tous les statuts --')] + Quote.STATUS_CHOICES,
                              required=False, widget=forms.Select(attrs={'class': 'form-control'}),
                              label="Statut")
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
                               label="Du")
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
                             label="Au")


class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = ['template_type', 'subject', 'body', 'is_active']
        widgets = {
            'template_type': forms.Select(attrs={'class': 'form-control', 'disabled': 'disabled'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sujet du email'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Contenu HTML du email\nVariables disponibles: {invoice_number}, {quote_number}, {date}, {due_date}, {validity_date}, {total}, {custom_message}'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SendEmailForm(forms.Form):
    recipient_email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email du destinataire'}),
        label="Email destinataire"
    )
    custom_message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Message personnalisé (optionnel)'}),
        label="Message personnalisé"
    )
    attach_pdf = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Joindre le PDF"
    )


# ============================================================================
# TIER 3 - BONUS MASTER: Forms pour IA/Intelligence & Synchronisation
# ============================================================================

class AnomalyFilterForm(forms.Form):
    """Filtrer les anomalies détectées"""
    anomaly_type = forms.ChoiceField(
        choices=[('', '-- Tous les types --')] + AnomalyDetection.ANOMALY_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Type d'anomalie"
    )
    severity = forms.ChoiceField(
        choices=[('', '-- Toutes sévérités --')] + AnomalyDetection.SEVERITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Sévérité"
    )
    is_resolved = forms.NullBooleanField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}, choices=[(None, '-- Tous --'), (True, 'Résolu'), (False, 'Non résolu')]),
        label="Statut"
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Du"
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Au"
    )


class IntelligentAlertFilterForm(forms.Form):
    """Filtrer les alertes intelligentes"""
    alert_type = forms.ChoiceField(
        choices=[('', '-- Tous les types --')] + IntelligentAlert.ALERT_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Type d'alerte"
    )
    priority = forms.ChoiceField(
        choices=[('', '-- Toutes priorités --')] + IntelligentAlert.PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Priorité"
    )
    is_acknowledged = forms.NullBooleanField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}, choices=[(None, '-- Tous --'), (True, 'Confirmé'), (False, 'Non confirmé')]),
        label="Statut"
    )


class RevenueForecastForm(forms.ModelForm):
    """Créer/modifier une prévision de CA"""
    class Meta:
        model = RevenueForecast
        fields = ['period', 'forecast_date', 'predicted_revenue', 'predicted_invoices']
        widgets = {
            'period': forms.Select(attrs={'class': 'form-control'}),
            'forecast_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'predicted_revenue': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'CA prédit (€)'}),
            'predicted_invoices': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de factures'}),
        }


class AccountingSynchronizationForm(forms.Form):
    """Formulaire pour exporter données comptables"""
    export_type = forms.ChoiceField(
        choices=AccountingSynchronization.EXPORT_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Type d'export"
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Date de début"
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Date de fin"
    )
    format = forms.ChoiceField(
        choices=[('csv', 'CSV'), ('xlsx', 'Excel'), ('json', 'JSON')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Format d'export"
    )


class AnomalyResolutionForm(forms.ModelForm):
    """Formulaire pour résoudre une anomalie"""
    class Meta:
        model = AnomalyDetection
        fields = ['is_resolved', 'resolution_notes']
        widgets = {
            'is_resolved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'resolution_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Notes de résolution'}),
        }


class IntelligentAlertAcknowledgeForm(forms.ModelForm):
    """Formulaire pour confirmer une alerte"""
    class Meta:
        model = IntelligentAlert
        fields = ['is_acknowledged']
        widgets = {
            'is_acknowledged': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class NotificationFilterForm(forms.Form):
    type = forms.ChoiceField(
        choices=[('', '-- Tous les types --')] + Notification.TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Type de notification"
    )
    status = forms.ChoiceField(
        choices=[('', '-- Tous les statuts --')] + Notification.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Statut"
    )
    client = forms.ModelChoiceField(
        queryset=Client.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Client"
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Du"
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Au"
    )
