from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from datetime import datetime, timedelta

class Client(models.Model):
    """Client model"""
    name = models.CharField(max_length=255, verbose_name="Nom du client")
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    delivery_address = models.TextField(blank=True, null=True, verbose_name="Adresse de livraison")
    billing_address = models.TextField(blank=True, null=True, verbose_name="Adresse de facturation")
    country = models.CharField(max_length=100, default="France", verbose_name="Pays")
    tva_intra = models.CharField(max_length=50, blank=True, null=True, verbose_name="Numéro TVA Intracommunautaire")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """Product model"""
    name = models.CharField(max_length=255, verbose_name="Nom du produit")
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="Prix")
    reference = models.CharField(max_length=100, unique=True, verbose_name="Référence")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class CompanyInfo(models.Model):
    """Company information model"""
    name = models.CharField(max_length=255, verbose_name="Nom de l'entreprise")
    address = models.TextField(blank=True, null=True, verbose_name="Adresse")
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    siret = models.CharField(max_length=14, blank=True, null=True, verbose_name="SIRET")
    siren = models.CharField(max_length=9, blank=True, null=True, verbose_name="SIREN")
    tva_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Numéro TVA")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True, verbose_name="Logo")
    country = models.CharField(max_length=100, default="France")
    
    class Meta:
        verbose_name = "Information Entreprise"
        verbose_name_plural = "Informations Entreprise"
    
    def __str__(self):
        return self.name or "Informations Entreprise"


class Invoice(models.Model):
    """Invoice model"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('paid', 'Payée'),
        ('partial', 'Partiellement payée'),
        ('overdue', 'En retard'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', 'Virement bancaire'),
        ('check', 'Chèque'),
        ('cash', 'Espèces'),
        ('card', 'Carte bancaire'),
        ('other', 'Autre'),
    ]
    
    invoice_number = models.CharField(max_length=20, unique=True, verbose_name="Numéro de facture")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices', verbose_name="Client")
    date = models.DateField(default=datetime.now, verbose_name="Date")
    due_date = models.DateField(verbose_name="Date d'échéance")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='bank_transfer')
    
    # Calculations
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Sous-total")
    
    # Remise (discount)
    remise_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Remise %")
    remise_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Montant remise")
    
    # Rabais (rebate)
    rabais_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Rabais %")
    rabais_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Montant rabais")
    
    # Escompte (early payment discount)
    escompte_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Escompte %")
    escompte_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Montant escompte")
    
    total_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Réduction totale")
    tva_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Montant TVA")
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total")
    
    # Payment tracking
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Montant payé")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name="Statut")
    
    # Credit notes
    is_credit_note = models.BooleanField(default=False, verbose_name="Avoir")
    credit_note_reason = models.TextField(blank=True, null=True, verbose_name="Raison de l'avoir")
    original_invoice = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='credit_notes', verbose_name="Facture originale")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Facture"
        verbose_name_plural = "Factures"
        ordering = ['-date']
    
    def __str__(self):
        return f"Facture {self.invoice_number}"
    
    @property
    def remaining_amount(self):
        """Calculate remaining amount to pay"""
        return max(0, self.total - self.amount_paid)
    
    def update_payment_status(self):
        """Update payment status based on amount paid"""
        if self.amount_paid >= self.total:
            self.payment_status = 'paid'
        elif self.amount_paid > 0:
            self.payment_status = 'partial'
        elif self.due_date < datetime.now().date():
            self.payment_status = 'overdue'
        else:
            self.payment_status = 'pending'


class InvoiceItem(models.Model):
    """Invoice line item"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items', verbose_name="Facture")
    description = models.CharField(max_length=255, verbose_name="Description")
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)], verbose_name="Quantité")
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="Prix unitaire")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Produit")
    
    class Meta:
        verbose_name = "Ligne de facture"
        verbose_name_plural = "Lignes de facture"
    
    def __str__(self):
        return f"{self.description} x{self.quantity}"
    
    @property
    def total(self):
        """Calculate line total"""
        return self.quantity * self.price


class Payment(models.Model):
    """Payment record"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments', verbose_name="Facture")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Montant")
    payment_method = models.CharField(max_length=20, verbose_name="Méthode de paiement")
    payment_date = models.DateField(default=datetime.now, verbose_name="Date de paiement")
    reference = models.CharField(max_length=100, blank=True, null=True, verbose_name="Référence")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Paiement {self.amount}€ - {self.invoice.invoice_number}"


class Quote(models.Model):
    """Quote/Devis model"""
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('sent', 'Envoyé'),
        ('accepted', 'Accepté'),
        ('rejected', 'Rejeté'),
        ('expired', 'Expiré'),
        ('converted', 'Converti en facture'),
    ]
    
    quote_number = models.CharField(max_length=20, unique=True, verbose_name="Numéro de devis")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='quotes', verbose_name="Client")
    date = models.DateField(default=datetime.now, verbose_name="Date du devis")
    validity_date = models.DateField(verbose_name="Date de validité")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Statut")
    
    # Calculations
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Sous-total")
    
    # Remise (discount)
    remise_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Remise %")
    remise_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Montant remise")
    
    # Rabais (rebate)
    rabais_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Rabais %")
    rabais_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Montant rabais")
    
    # Escompte (early payment discount)
    escompte_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Escompte %")
    escompte_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Montant escompte")
    
    total_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Réduction totale")
    tva_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Montant TVA")
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total")
    
    # Notes and terms
    terms_conditions = models.TextField(blank=True, null=True, verbose_name="Conditions générales")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    
    # Link to converted invoice
    converted_invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, blank=True, null=True, 
                                         related_name='quote_source', verbose_name="Facture générée")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Devis"
        verbose_name_plural = "Devis"
        ordering = ['-date']
    
    def __str__(self):
        return f"Devis {self.quote_number}"
    
    @property
    def is_expired(self):
        """Check if quote is expired"""
        return datetime.now().date() > self.validity_date and self.status != 'converted'


class QuoteItem(models.Model):
    """Quote line item"""
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name='items', verbose_name="Devis")
    description = models.CharField(max_length=255, verbose_name="Description")
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)], verbose_name="Quantité")
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="Prix unitaire")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Produit")
    
    class Meta:
        verbose_name = "Ligne de devis"
        verbose_name_plural = "Lignes de devis"
    
    def __str__(self):
        return f"{self.description} x{self.quantity}"
    
    @property
    def total(self):
        """Calculate line total"""
        return self.quantity * self.price


class Notification(models.Model):
    """Notification model"""
    TYPE_CHOICES = [
        ('invoice_created', 'Facture créée'),
        ('invoice_sent', 'Facture envoyée'),
        ('invoice_paid', 'Facture payée'),
        ('invoice_overdue', 'Facture en retard'),
        ('quote_created', 'Devis créé'),
        ('quote_accepted', 'Devis accepté'),
        ('quote_rejected', 'Devis rejeté'),
        ('payment_received', 'Paiement reçu'),
        ('reminder', 'Rappel'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('sent', 'Envoyé'),
        ('failed', 'Échoué'),
        ('read', 'Lu'),
    ]
    
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, verbose_name="Type")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Statut")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='notifications', verbose_name="Client")
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, blank=True, null=True, related_name='notifications', verbose_name="Facture")
    quote = models.ForeignKey(Quote, on_delete=models.SET_NULL, blank=True, null=True, related_name='notifications', verbose_name="Devis")
    
    subject = models.CharField(max_length=255, verbose_name="Sujet")
    message = models.TextField(verbose_name="Message")
    recipient_email = models.EmailField(verbose_name="Email du destinataire")
    
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True, verbose_name="Date d'envoi")
    error_message = models.TextField(blank=True, null=True, verbose_name="Message d'erreur")
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', '-created_at']),
            models.Index(fields=['status', 'type']),
        ]
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.client.name}"


class EmailTemplate(models.Model):
    """Email template model"""
    TEMPLATE_CHOICES = [
        ('invoice_created', 'Facture créée'),
        ('invoice_sent', 'Facture envoyée'),
        ('invoice_reminder', 'Rappel facture'),
        ('quote_sent', 'Devis envoyé'),
        ('quote_accepted', 'Confirmation acceptation devis'),
        ('payment_thank_you', 'Remerciement paiement'),
    ]
    
    template_type = models.CharField(max_length=50, choices=TEMPLATE_CHOICES, unique=True, verbose_name="Type de template")
    subject = models.CharField(max_length=255, verbose_name="Sujet")
    body = models.TextField(verbose_name="Contenu du email (HTML)")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Template Email"
        verbose_name_plural = "Templates Email"
    
    def __str__(self):
        return self.get_template_type_display()


class AuditLog(models.Model):
    """Audit trail for tracking all modifications"""
    ACTION_CHOICES = [
        ('create', 'Créé'),
        ('update', 'Modifié'),
        ('delete', 'Supprimé'),
        ('view', 'Consulté'),
    ]
    
    MODEL_CHOICES = [
        ('Client', 'Client'),
        ('Product', 'Produit'),
        ('Invoice', 'Facture'),
        ('InvoiceItem', 'Ligne Facture'),
        ('Payment', 'Paiement'),
        ('Quote', 'Devis'),
        ('QuoteItem', 'Ligne Devis'),
        ('CompanyInfo', 'Info Entreprise'),
        ('Notification', 'Notification'),
        ('EmailTemplate', 'Template Email'),
    ]
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="Action")
    model = models.CharField(max_length=50, choices=MODEL_CHOICES, verbose_name="Modèle")
    object_id = models.IntegerField(verbose_name="ID de l'objet")
    object_str = models.CharField(max_length=255, blank=True, null=True, verbose_name="Objet (str)")
    user = models.CharField(max_length=255, blank=True, null=True, verbose_name="Utilisateur")
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="Adresse IP")
    old_values = models.JSONField(default=dict, blank=True, verbose_name="Anciennes valeurs")
    new_values = models.JSONField(default=dict, blank=True, verbose_name="Nouvelles valeurs")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Date/Heure")
    
    class Meta:
        verbose_name = "Journal d'audit"
        verbose_name_plural = "Journaux d'audit"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['model', 'object_id']),
            models.Index(fields=['-timestamp']),
            models.Index(fields=['action']),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.get_model_display()} (#{self.object_id}) by {self.user or 'Anonymous'}"


# ============================================================================
# TIER 3 - BONUS MASTER 🔥: IA/Intelligence & Synchronisation Comptable
# ============================================================================

class AnomalyDetection(models.Model):
    """IA: Détection automatique des anomalies"""
    ANOMALY_TYPES = [
        ('unusual_amount', 'Montant anormal'),
        ('payment_delay', 'Retard de paiement'),
        ('duplicate_invoice', 'Facture en doublon'),
        ('unusual_client', 'Client inhabituel'),
        ('pricing_error', 'Erreur de tarification'),
        ('unusual_frequency', 'Fréquence anormale'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Basse'),
        ('medium', 'Moyenne'),
        ('high', 'Haute'),
        ('critical', 'Critique'),
    ]
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, verbose_name="Facture")
    anomaly_type = models.CharField(max_length=50, choices=ANOMALY_TYPES, verbose_name="Type d'anomalie")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, verbose_name="Sévérité")
    description = models.TextField(verbose_name="Description de l'anomalie")
    detected_value = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valeur détectée")
    expected_value = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valeur attendue")
    confidence = models.DecimalField(max_digits=3, decimal_places=2, validators=[MinValueValidator(0), MinValueValidator(100)], verbose_name="Confiance %")
    is_resolved = models.BooleanField(default=False, verbose_name="Résolu")
    resolved_at = models.DateTimeField(blank=True, null=True, verbose_name="Date de résolution")
    resolution_notes = models.TextField(blank=True, null=True, verbose_name="Notes de résolution")
    detected_at = models.DateTimeField(auto_now_add=True, verbose_name="Détecté le")
    
    class Meta:
        verbose_name = "Détection d'anomalie"
        verbose_name_plural = "Détections d'anomalies"
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['invoice', 'severity']),
            models.Index(fields=['is_resolved', '-detected_at']),
            models.Index(fields=['anomaly_type']),
        ]
    
    def __str__(self):
        return f"{self.get_anomaly_type_display()} - {self.invoice.number} ({self.get_severity_display()})"


class RevenueForecast(models.Model):
    """IA: Prévisions de chiffre d'affaires"""
    FORECAST_PERIOD = [
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuelle'),
        ('quarterly', 'Trimestrielle'),
        ('yearly', 'Annuelle'),
    ]
    
    period = models.CharField(max_length=20, choices=FORECAST_PERIOD, verbose_name="Période")
    forecast_date = models.DateField(verbose_name="Date de la prévision")
    predicted_revenue = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="CA prédit")
    predicted_invoices = models.IntegerField(verbose_name="Factures prévues")
    confidence_interval_low = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Intervalle bas")
    confidence_interval_high = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Intervalle haut")
    actual_revenue = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="CA réel")
    actual_invoices = models.IntegerField(blank=True, null=True, verbose_name="Factures réelles")
    accuracy = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0), MinValueValidator(100)], verbose_name="Précision %")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Prévision de CA"
        verbose_name_plural = "Prévisions de CA"
        ordering = ['-forecast_date']
        unique_together = ('period', 'forecast_date')
        indexes = [
            models.Index(fields=['period', 'forecast_date']),
        ]
    
    def __str__(self):
        return f"{self.get_period_display()} - {self.forecast_date}: {self.predicted_revenue}€"


class IntelligentAlert(models.Model):
    """IA: Alertes intelligentes basées sur IA"""
    ALERT_TYPES = [
        ('anomaly', 'Anomalie détectée'),
        ('forecast_warning', 'Avertissement prévisions'),
        ('payment_risk', 'Risque de paiement'),
        ('revenue_decline', 'Baisse de revenus'),
        ('unusual_pattern', 'Motif inhabituél'),
        ('duplicate_detection', 'Doublon détecté'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Basse'),
        ('medium', 'Moyenne'),
        ('high', 'Haute'),
        ('urgent', 'Urgent'),
    ]
    
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES, verbose_name="Type d'alerte")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, verbose_name="Priorité")
    title = models.CharField(max_length=255, verbose_name="Titre")
    description = models.TextField(verbose_name="Description")
    related_invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Facture associée")
    related_client = models.ForeignKey(Client, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Client associé")
    recommendation = models.TextField(blank=True, null=True, verbose_name="Recommandation IA")
    is_acknowledged = models.BooleanField(default=False, verbose_name="Confirmé")
    acknowledged_by = models.CharField(max_length=255, blank=True, null=True, verbose_name="Confirmé par")
    acknowledged_at = models.DateTimeField(blank=True, null=True, verbose_name="Confirmé le")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    
    class Meta:
        verbose_name = "Alerte intelligente"
        verbose_name_plural = "Alertes intelligentes"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['priority', 'is_acknowledged']),
            models.Index(fields=['alert_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.get_priority_display()}: {self.title}"


class AccountingSynchronization(models.Model):
    """Synchronisation comptable: Export CSV et intégration"""
    EXPORT_TYPES = [
        ('invoices', 'Factures'),
        ('payments', 'Paiements'),
        ('clients', 'Clients'),
        ('products', 'Produits'),
        ('journal', 'Journal comptable'),
        ('trial_balance', 'Balance trial'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
    ]
    
    export_type = models.CharField(max_length=50, choices=EXPORT_TYPES, verbose_name="Type d'export")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Statut")
    start_date = models.DateField(verbose_name="Date de début")
    end_date = models.DateField(verbose_name="Date de fin")
    records_count = models.IntegerField(default=0, verbose_name="Nombre d'enregistrements")
    file_path = models.CharField(max_length=500, blank=True, null=True, verbose_name="Chemin fichier")
    file_size = models.BigIntegerField(blank=True, null=True, verbose_name="Taille fichier (bytes)")
    checksum = models.CharField(max_length=64, blank=True, null=True, verbose_name="Checksum SHA256")
    error_message = models.TextField(blank=True, null=True, verbose_name="Message d'erreur")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name="Complété le")
    created_by = models.CharField(max_length=255, blank=True, null=True, verbose_name="Créé par")
    
    class Meta:
        verbose_name = "Synchronisation comptable"
        verbose_name_plural = "Synchronisations comptables"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['export_type', 'status']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_export_type_display()} ({self.get_status_display()}) - {self.start_date} à {self.end_date}"
