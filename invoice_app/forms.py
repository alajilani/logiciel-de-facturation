from django import forms
from .models import Client, Product, Invoice, InvoiceItem, Payment, CompanyInfo, Quote, QuoteItem, Notification, EmailTemplate
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
        fields = ['name', 'price', 'reference', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du produit'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Prix', 'step': '0.01'}),
            'reference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Référence'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description'}),
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


# ============== TIER 2 Forms ==============

class ArchiveForm(forms.Form):
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Raison de l''archivage'}),
        label='Raison'
    )


class UnarchiveForm(forms.Form):
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Raison de la restauration'}),
        label='Raison'
    )


class AdvancedSearchForm(forms.Form):
    SEARCH_TYPES = [
        ('all', 'Tous les types'),
        ('invoice', 'Factures'),
        ('client', 'Clients'),
        ('quote', 'Devis'),
    ]
    
    search_text = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rechercher...'}),
        label='Texte',
        required=False
    )
    search_type = forms.ChoiceField(
        choices=SEARCH_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Type',
        required=False
    )
    date_from = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Date debut',
        required=False
    )
    date_to = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Date fin',
        required=False
    )


class ExchangeRateForm(forms.Form):
    CURRENCY_CHOICES = [
        ('EUR', 'Euro (EUR)'),
        ('USD', 'Dollar US (USD)'),
        ('GBP', 'Livre Sterling (GBP)'),
    ]
    
    from_currency = forms.ChoiceField(
        choices=CURRENCY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='De (Devise source)'
    )
    to_currency = forms.ChoiceField(
        choices=CURRENCY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Vers (Devise cible)'
    )
    rate = forms.DecimalField(
        max_digits=8,
        decimal_places=4,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Taux de change', 'step': '0.0001'}),
        label='Taux de change'
    )

