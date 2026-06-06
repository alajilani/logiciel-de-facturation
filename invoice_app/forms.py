from django import forms
from .models import (
    Client, Product, Invoice, InvoiceItem, Payment, Quote, QuoteItem, 
    Notification, EmailTemplate, CategorieProduit
)
from django.conf import settings
from datetime import timedelta
import re

class ClientForm(forms.ModelForm):
    """Professional client form with conditional fields"""
    
    class Meta:
        model = Client
        fields = [
            'type_client', 'nom', 'raison_sociale', 'contact_principal', 'email', 'telephone',
            'adresse_facturation', 'code_postal_facturation', 'ville_facturation', 'pays_facturation',
            'livraison_identique_facturation',
            'adresse_livraison', 'code_postal_livraison', 'ville_livraison', 'pays_livraison',
            'numero_tva_intracommunautaire', 'siret_siren',
            'conditions_paiement', 'statut', 'notes_internes'
        ]
        widgets = {
            'type_client': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'nom': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Nom du client',
                'required': 'required'
            }),
            'raison_sociale': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Raison sociale (obligatoire pour entreprise)'
            }),
            'contact_principal': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Nom du contact principal'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 
                'placeholder': 'email@example.com'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '+33 1 23 45 67 89'
            }),
            # Facturation
            'adresse_facturation': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2, 
                'placeholder': 'Adresse complète de facturation',
                'required': 'required'
            }),
            'code_postal_facturation': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '75001',
                'required': 'required'
            }),
            'ville_facturation': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Paris',
                'required': 'required'
            }),
            'pays_facturation': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'France'
            }),
            'livraison_identique_facturation': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'livraison_identique'
            }),
            # Livraison
            'adresse_livraison': forms.Textarea(attrs={
                'class': 'form-control livraison-field', 
                'rows': 2, 
                'placeholder': 'Adresse de livraison'
            }),
            'code_postal_livraison': forms.TextInput(attrs={
                'class': 'form-control livraison-field', 
                'placeholder': '75001'
            }),
            'ville_livraison': forms.TextInput(attrs={
                'class': 'form-control livraison-field', 
                'placeholder': 'Paris'
            }),
            'pays_livraison': forms.TextInput(attrs={
                'class': 'form-control livraison-field', 
                'placeholder': 'France'
            }),
            # Fiscal
            'numero_tva_intracommunautaire': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'FR12345678901'
            }),
            'siret_siren': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'SIRET/SIREN'
            }),
            # Gestion
            'conditions_paiement': forms.Select(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'notes_internes': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Notes internes'
            }),
        }
    
    def clean(self):
        """Validate business rules"""
        cleaned_data = super().clean()
        type_client = cleaned_data.get('type_client')
        raison_sociale = cleaned_data.get('raison_sociale')

        if type_client == 'ENTREPRISE':
            # ENTREPRISE requires raison_sociale
            if not raison_sociale:
                self.add_error('raison_sociale', 'La raison sociale est obligatoire pour une entreprise.')
        elif type_client == 'PARTICULIER':
            # PARTICULIER: clear entreprise-only fields, ignore any submitted values
            cleaned_data['raison_sociale'] = ''
            cleaned_data['numero_tva_intracommunautaire'] = ''
            cleaned_data['siret_siren'] = ''
            # Strip errors that may have been raised on those fields
            for f in ('raison_sociale', 'numero_tva_intracommunautaire', 'siret_siren'):
                if f in self._errors:
                    del self._errors[f]

        return cleaned_data


class ProductForm(forms.ModelForm):
    prix_unitaire_ttc = forms.DecimalField(
        label="Prix unitaire TTC",
        required=False,
        disabled=True,
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly', 'step': '0.01'})
    )

    class Meta:
        model = Product
        fields = [
            'name', 'reference', 'type_item', 'categorie', 'description',
            'prix_unitaire_ht', 'taux_tva', 'unite',
            'suivre_stock', 'stock', 'seuil_alerte', 'disponible_vente', 'statut'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'reference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Référence (unique si renseignée)'}),
            'type_item': forms.Select(attrs={'class': 'form-control'}),
            'categorie': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description'}),
            'prix_unitaire_ht': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Prix unitaire HT', 'step': '0.01'}),
            'taux_tva': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Taux TVA', 'step': '0.01'}),
            'unite': forms.Select(attrs={'class': 'form-control'}),
            'suivre_stock': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'seuil_alerte': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'disponible_vente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categorie'].queryset = CategorieProduit.objects.filter(statut='ACTIF').order_by('nom')
        if self.instance and self.instance.pk:
            self.fields['prix_unitaire_ttc'].initial = self.instance.prix_unitaire_ttc

    def clean(self):
        cleaned_data = super().clean()
        type_item = cleaned_data.get('type_item')
        suivre_stock = cleaned_data.get('suivre_stock')
        prix_ht = cleaned_data.get('prix_unitaire_ht') or 0
        taux_tva = cleaned_data.get('taux_tva') or 0

        # Services: stock management disabled.
        if type_item == 'SERVICE':
            cleaned_data['suivre_stock'] = False
            cleaned_data['stock'] = 0
            cleaned_data['seuil_alerte'] = 0
        elif not suivre_stock:
            cleaned_data['stock'] = 0
            cleaned_data['seuil_alerte'] = 0

        # Display-only TTC in form, real computation remains in model save().
        self.fields['prix_unitaire_ttc'].initial = prix_ht + (prix_ht * taux_tva / 100)
        return cleaned_data


class CategorieProduitForm(forms.ModelForm):
    class Meta:
        model = CategorieProduit
        fields = ['nom', 'description', 'statut']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de la catégorie'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description (optionnelle)'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
        }


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['client', 'date', 'due_date', 'payment_method', 'notes']
        labels = {
            'payment_method': 'Mode de règlement prévu',
        }
        widgets = {
            'client': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notes internes de la facture'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Due date can be left empty: backend will auto-compute from client's payment terms.
        self.fields['due_date'].required = False
        # Force ISO input formats so HTML5 type=date inputs (and Flatpickr) work
        # consistently regardless of the project LANGUAGE_CODE / USE_L10N setting.
        self.fields['date'].input_formats = ['%Y-%m-%d']
        self.fields['due_date'].input_formats = ['%Y-%m-%d']
        # On unbound forms (create), pre-fill date with today so the user has a sane default.
        if not self.is_bound and not self.instance.pk:
            from datetime import date as _date
            self.fields['date'].initial = _date.today()

    @staticmethod
    def compute_due_date(client, base_date):
        """Compute due_date from a client's conditions_paiement + an invoice date.
        IMMEDIAT -> same day. Any 'N_JOURS' choice -> +N days. Fallback +30 days."""
        if not client or not base_date:
            return None
        cond = (getattr(client, 'conditions_paiement', None) or 'IMMEDIAT').upper()
        if cond == 'IMMEDIAT':
            return base_date
        match = re.match(r'^(\d+)_JOURS$', cond)
        days = int(match.group(1)) if match else 30
        return base_date + timedelta(days=days)

    def clean(self):
        cleaned = super().clean()
        # Auto-compute due_date when missing — single source of truth backend.
        if not cleaned.get('due_date'):
            computed = self.compute_due_date(cleaned.get('client'), cleaned.get('date'))
            if computed:
                cleaned['due_date'] = computed
                if 'due_date' in self._errors:
                    del self._errors['due_date']
        return cleaned


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['produit_service', 'description', 'quantite', 'prix_unitaire_ht', 'taux_tva', 'unite', 'remise_pourcentage']
        widgets = {
            'produit_service': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Description de la ligne'}),
            'quantite': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Quantité', 'min': '0.01', 'step': '0.01'}),
            'prix_unitaire_ht': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Prix unitaire HT', 'step': '0.01'}),
            'taux_tva': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Taux TVA', 'step': '0.01'}),
            'unite': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Unité'}),
            'remise_pourcentage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Remise %', 'step': '0.01', 'min': '0', 'max': '100'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['produit_service'].queryset = Product.objects.filter(statut='ACTIF', disponible_vente=True).order_by('name')


class InvoiceDiscountForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['remise_globale_pourcentage', 'remise_globale_montant']
        widgets = {
            'remise_globale_pourcentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '%', 'min': '0'}),
            'remise_globale_montant': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Montant €', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Both discount fields are optional: the user fills ONE of the two.
        # If they leave both blank/missing in POST, treat as zero (= no discount).
        from decimal import Decimal
        for fname in ('remise_globale_pourcentage', 'remise_globale_montant'):
            self.fields[fname].required = False
            self.fields[fname].initial = self.fields[fname].initial or Decimal('0')

    def clean_remise_globale_pourcentage(self):
        from decimal import Decimal
        v = self.cleaned_data.get('remise_globale_pourcentage')
        return v if v is not None else Decimal('0')

    def clean_remise_globale_montant(self):
        from decimal import Decimal
        v = self.cleaned_data.get('remise_globale_montant')
        return v if v is not None else Decimal('0')

    def clean(self):
        cleaned_data = super().clean()
        remise_pct = cleaned_data.get('remise_globale_pourcentage') or 0
        remise_montant = cleaned_data.get('remise_globale_montant') or 0

        if remise_pct and remise_montant and float(remise_pct) > 0 and float(remise_montant) > 0:
            raise forms.ValidationError('La remise globale en % et en montant ne peuvent pas être utilisées en même temps.')

        sous_total = getattr(self.instance, 'sous_total_ht', 0) or 0
        if remise_montant and sous_total and remise_montant > sous_total:
            raise forms.ValidationError('La remise globale ne peut pas dépasser le sous-total HT.')

        return cleaned_data


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_method', 'payment_date', 'reference', 'notes']
        labels = {
            'payment_method': 'Méthode de paiement utilisée',
        }
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Montant'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'reference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Référence'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notes'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_date'].input_formats = ['%Y-%m-%d']


class InvoiceFilterForm(forms.Form):
    client = forms.ModelChoiceField(queryset=Client.objects.all(), required=False, 
                                   widget=forms.Select(attrs={'class': 'form-control'}),
                                   label="Client")
    statut = forms.ChoiceField(choices=[('', '-- Tous les statuts --')] + Invoice.STATUT_CHOICES,
                               required=False, widget=forms.Select(attrs={'class': 'form-control'}),
                               label="Statut")
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
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'validity_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'terms_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Conditions générales'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notes'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].input_formats = ['%Y-%m-%d']
        self.fields['validity_date'].input_formats = ['%Y-%m-%d']


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
    type_notification = forms.ChoiceField(
        choices=[('', '-- Tous les types --')] + Notification.TYPE_NOTIFICATION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Type de notification"
    )
    niveau = forms.ChoiceField(
        choices=[('', '-- Tous les niveaux --')] + Notification.NIVEAU_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Priorité"
    )
    lu = forms.ChoiceField(
        choices=[('', '-- Lu / Non lu --'), ('non_lu', 'Non lues'), ('lu', 'Lues')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Lecture"
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
