

# ============== Tier 2: Multi-Currency & Search & Archiving ==============

class ExchangeRate(models.Model):
    """Exchange rates for multi-currency support"""
    CURRENCY_CHOICES = [
        ('EUR', 'Euro'),
        ('USD', 'US Dollar'),
        ('GBP', 'British Pound'),
    ]
    
    from_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, verbose_name="Devise source")
    to_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, verbose_name="Devise cible")
    rate = models.DecimalField(max_digits=8, decimal_places=4, verbose_name="Taux de change")
    date = models.DateField(default=datetime.now, verbose_name="Date du taux")
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Taux de change"
        verbose_name_plural = "Taux de change"
        unique_together = ('from_currency', 'to_currency', 'date')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['from_currency', 'to_currency', '-date']),
        ]
    
    def __str__(self):
        return f"{self.from_currency} to {self.to_currency}: {self.rate}"


class SearchIndex(models.Model):
    """Full-text search index for invoices and clients"""
    CONTENT_TYPE_CHOICES = [
        ('invoice', 'Facture'),
        ('client', 'Client'),
        ('quote', 'Devis'),
    ]
    
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES, verbose_name="Type de contenu")
    object_id = models.IntegerField(verbose_name="ID de l'objet")
    
    # Full-text searchable fields
    search_text = models.TextField(verbose_name="Texte de recherche")
    keywords = models.TextField(verbose_name="Mots-cles")
    
    # Reference fields
    document_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Numero du document")
    client_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nom du client")
    amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Montant")
    date = models.DateField(blank=True, null=True, verbose_name="Date")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Index de recherche"
        verbose_name_plural = "Index de recherche"
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['search_text']),
            models.Index(fields=['keywords']),
            models.Index(fields=['document_number']),
            models.Index(fields=['client_name']),
        ]
    
    def __str__(self):
        return f"{self.get_content_type_display()} #{self.object_id}"


class ArchiveLog(models.Model):
    """Track archived invoices"""
    invoice = models.OneToOneField(Invoice, on_delete=models.CASCADE, related_name='archive_log', 
                                   verbose_name="Facture")
    
    archived_by = models.CharField(max_length=255, blank=True, null=True, verbose_name="Archivee par")
    archived_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'archivage")
    reason = models.TextField(blank=True, null=True, verbose_name="Raison de l'archivage")
    
    # For restoration
    unarchived_by = models.CharField(max_length=255, blank=True, null=True, verbose_name="Restauree par")
    unarchived_at = models.DateTimeField(blank=True, null=True, verbose_name="Date de restauration")
    unarchive_reason = models.TextField(blank=True, null=True, verbose_name="Raison de la restauration")
    
    class Meta:
        verbose_name = "Journal d'archivage"
        verbose_name_plural = "Journaux d'archivage"
        ordering = ['-archived_at']
    
    def __str__(self):
        status = "Restauree" if self.unarchived_at else "Archivee"
        return f"{self.invoice.invoice_number} - {status}"
