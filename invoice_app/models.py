from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from datetime import datetime, timedelta
from django.utils import timezone

class Client(models.Model):
    """Client model - Professional invoice management"""
    
    # Type de client
    TYPE_CLIENT_CHOICES = [
        ('PARTICULIER', 'Particulier'),
        ('ENTREPRISE', 'Entreprise'),
    ]
    
    # Conditions de paiement
    CONDITIONS_PAIEMENT_CHOICES = [
        ('IMMEDIAT', 'Paiement immédiat'),
        ('15_JOURS', '15 jours'),
        ('30_JOURS', '30 jours'),
    ]
    
    # Statut du client
    STATUT_CHOICES = [
        ('ACTIF', 'Actif'),
        ('INACTIF', 'Inactif'),
    ]
    
    # Informations générales
    type_client = models.CharField(
        max_length=20, 
        choices=TYPE_CLIENT_CHOICES, 
        default='PARTICULIER',
        verbose_name="Type de client"
    )
    nom = models.CharField(max_length=255, verbose_name="Nom")
    raison_sociale = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        verbose_name="Raison sociale"
    )
    contact_principal = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        verbose_name="Contact principal"
    )
    email = models.EmailField(blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    
    # Adresse de facturation
    adresse_facturation = models.TextField(verbose_name="Adresse de facturation")
    code_postal_facturation = models.CharField(max_length=10, verbose_name="Code postal")
    ville_facturation = models.CharField(max_length=100, verbose_name="Ville")
    pays_facturation = models.CharField(
        max_length=100, 
        default="France", 
        verbose_name="Pays"
    )
    
    # Adresse de livraison
    adresse_livraison = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Adresse de livraison"
    )
    code_postal_livraison = models.CharField(
        max_length=10, 
        blank=True, 
        null=True, 
        verbose_name="Code postal (livraison)"
    )
    ville_livraison = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        verbose_name="Ville (livraison)"
    )
    pays_livraison = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        verbose_name="Pays (livraison)"
    )
    livraison_identique_facturation = models.BooleanField(
        default=True, 
        verbose_name="Livraison identique à facturation"
    )
    
    # Informations fiscales
    numero_tva_intracommunautaire = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        verbose_name="Numéro TVA intracommunautaire"
    )
    siret_siren = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        verbose_name="SIRET/SIREN"
    )
    
    # Gestion
    conditions_paiement = models.CharField(
        max_length=20, 
        choices=CONDITIONS_PAIEMENT_CHOICES, 
        default='30_JOURS',
        verbose_name="Conditions de paiement"
    )
    statut = models.CharField(
        max_length=20, 
        choices=STATUT_CHOICES, 
        default='ACTIF',
        verbose_name="Statut"
    )
    notes_internes = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Notes internes"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    
    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['nom']
        indexes = [
            models.Index(fields=['statut']),
            models.Index(fields=['type_client']),
        ]
    
    def __str__(self):
        return f"{self.nom} ({self.get_type_client_display()})"
    
    def save(self, *args, **kwargs):
        """Override save to handle address synchronization"""
        if self.livraison_identique_facturation:
            self.adresse_livraison = self.adresse_facturation
            self.code_postal_livraison = self.code_postal_facturation
            self.ville_livraison = self.ville_facturation
            self.pays_livraison = self.pays_facturation
        super().save(*args, **kwargs)
    
    @property
    def adresse_complete_facturation(self):
        """Complete billing address"""
        parts = [
            self.adresse_facturation,
            f"{self.code_postal_facturation} {self.ville_facturation}",
            self.pays_facturation
        ]
        return "\n".join(filter(None, parts))
    
    @property
    def adresse_complete_livraison(self):
        """Complete delivery address"""
        if self.livraison_identique_facturation:
            return self.adresse_complete_facturation
        parts = [
            self.adresse_livraison,
            f"{self.code_postal_livraison} {self.ville_livraison}",
            self.pays_livraison
        ]
        return "\n".join(filter(None, parts))
    
    def is_active(self):
        """Check if client is active"""
        return self.statut == 'ACTIF'


class Product(models.Model):
    """Product / Service model with business rules

    - name : obligatoire
    - reference : unique si renseignée
    - type_item : PRODUIT ou SERVICE
    - categorie
    - description
    - prix_unitaire_ht
    - taux_tva
    - unite : PIECE, HEURE, JOUR, FORFAIT
    - suivre_stock
    - stock
    - seuil_alerte
    - statut : ACTIF / INACTIF
    """
    TYPE_ITEM_CHOICES = [
        ('PRODUIT', 'Produit'),
        ('SERVICE', 'Service'),
    ]

    UNITE_CHOICES = [
        ('PIECE', 'Pièce'),
        ('HEURE', 'Heure'),
        ('JOUR', 'Jour'),
        ('FORFAIT', 'Forfait'),
    ]

    STATUT_CHOICES = [
        ('ACTIF', 'Actif'),
        ('INACTIF', 'Inactif'),
    ]

    name = models.CharField(max_length=255, verbose_name="Nom")
    reference = models.CharField(max_length=100, blank=True, null=True, unique=True, verbose_name="Référence")
    type_item = models.CharField(max_length=10, choices=TYPE_ITEM_CHOICES, default='PRODUIT', verbose_name="Type")
    categorie = models.ForeignKey('CategorieProduit', on_delete=models.SET_NULL, blank=True, null=True, related_name='produits', verbose_name="Catégorie")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    prix_unitaire_ht = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], default=0, verbose_name="Prix unitaire HT")
    prix_unitaire_ttc = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False, verbose_name="Prix unitaire TTC")
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2, default=20.00, verbose_name="Taux TVA")
    unite = models.CharField(max_length=10, choices=UNITE_CHOICES, default='PIECE', verbose_name="Unité")
    suivre_stock = models.BooleanField(default=True, verbose_name="Suivre le stock")
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Stock")
    seuil_alerte = models.IntegerField(default=5, validators=[MinValueValidator(0)], verbose_name="Seuil d'alerte")
    disponible_vente = models.BooleanField(default=True, verbose_name="Disponible à la vente")
    derniere_modification_prix = models.DateTimeField(blank=True, null=True, verbose_name="Dernière modification du prix")
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='ACTIF', verbose_name="Statut")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Produit / Service"
        verbose_name_plural = "Produits / Services"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_type_item_display()})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if float(self.prix_unitaire_ht or 0) < 0:
            raise ValidationError({'prix_unitaire_ht': 'Le prix unitaire HT doit être supérieur ou égal à 0.'})
        if float(self.stock or 0) < 0:
            raise ValidationError({'stock': 'Le stock doit être supérieur ou égal à 0.'})
        if float(self.taux_tva or 0) < 0 or float(self.taux_tva or 0) > 100:
            raise ValidationError({'taux_tva': 'Le taux de TVA doit être entre 0 et 100.'})

        # Un service ne gère jamais le stock.
        if self.type_item == 'SERVICE':
            self.suivre_stock = False
            self.stock = 0
            self.seuil_alerte = 0
        elif not self.suivre_stock:
            self.stock = 0
            self.seuil_alerte = 0

    def calculate_prix_ttc(self):
        from decimal import Decimal, ROUND_HALF_UP
        prix_ht = Decimal(str(self.prix_unitaire_ht or 0))
        taux = Decimal(str(self.taux_tva or 0))
        tva = (prix_ht * taux / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.prix_unitaire_ttc = (prix_ht + tva).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def _generate_reference(self):
        year = timezone.now().year
        prefix = f"PRD-{year}-"
        latest = Product.objects.filter(reference__startswith=prefix).order_by('-reference').first()
        if latest and latest.reference:
            try:
                seq = int(latest.reference.split('-')[-1]) + 1
            except (TypeError, ValueError):
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @property
    def is_stock_faible(self):
        """Return True when stock is at or below the alert threshold."""
        return self.type_item == 'PRODUIT' and self.suivre_stock and self.stock <= self.seuil_alerte

    def can_allocate(self, quantity):
        """Check if the requested quantity can be allocated from stock."""
        if not self.disponible_vente:
            return False
        if self.type_item == 'SERVICE' or not self.suivre_stock:
            return True
        return self.stock >= quantity

    def decrease_stock(self, quantity):
        """Decrease stock when an order/invoice is validated."""
        if self.type_item == 'SERVICE' or not self.suivre_stock:
            return
        self.stock = max(0, self.stock - int(quantity))
        self.save(update_fields=['stock', 'updated_at'])

    def increase_stock(self, quantity):
        if self.type_item == 'SERVICE' or not self.suivre_stock:
            return
        self.stock = self.stock + int(quantity)
        self.save(update_fields=['stock', 'updated_at'])

    def save(self, *args, **kwargs):
        old_price = None
        if self.pk:
            old_price = Product.objects.filter(pk=self.pk).values_list('prix_unitaire_ht', flat=True).first()

        if not self.reference:
            self.reference = self._generate_reference()

        self.clean()
        self.calculate_prix_ttc()

        if old_price is not None and old_price != self.prix_unitaire_ht:
            self.derniere_modification_prix = timezone.now()
        elif old_price is None and self.prix_unitaire_ht is not None:
            self.derniere_modification_prix = timezone.now()

        super().save(*args, **kwargs)


class CategorieProduit(models.Model):
    """Catégorie métier pour produits et services."""
    STATUT_CHOICES = [
        ('ACTIF', 'Actif'),
        ('INACTIF', 'Inactif'),
    ]

    nom = models.CharField(max_length=120, unique=True, verbose_name="Nom")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='ACTIF', verbose_name="Statut")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Catégorie produit/service"
        verbose_name_plural = "Catégories produit/service"
        ordering = ['nom']

    def __str__(self):
        return self.nom


class CompanyInfo(models.Model):
    """Company information model"""
    name = models.CharField(max_length=255, verbose_name="Nom de l'entreprise")
    address = models.TextField(blank=True, null=True, verbose_name="Adresse")
    postal_code = models.CharField(max_length=20, blank=True, null=True, verbose_name="Code postal")
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ville")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone")
    email = models.EmailField(blank=True, null=True, verbose_name="Adresse email")
    website = models.URLField(blank=True, null=True, verbose_name="Site web")
    siret = models.CharField(max_length=14, blank=True, null=True, verbose_name="SIRET")
    siren = models.CharField(max_length=9, blank=True, null=True, verbose_name="SIREN")
    tva_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Numéro TVA intracommunautaire")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True, verbose_name="Logo")
    country = models.CharField(max_length=100, default="France", verbose_name="Pays")

    # Paramètres facturation
    currency = models.CharField(max_length=10, default="EUR", verbose_name="Devise")
    invoice_prefix = models.CharField(max_length=20, default="FAC-", blank=True, verbose_name="Préfixe facture")
    default_tva = models.DecimalField(max_digits=5, decimal_places=2, default=20, verbose_name="TVA par défaut (%)")
    default_payment_terms = models.CharField(
        max_length=255, blank=True, null=True,
        default="30 jours fin de mois",
        verbose_name="Conditions de paiement par défaut",
    )
    default_legal_mentions = models.TextField(
        blank=True, null=True,
        verbose_name="Mentions légales par défaut",
    )

    class Meta:
        verbose_name = "Information Entreprise"
        verbose_name_plural = "Informations Entreprise"

    def __str__(self):
        return self.name or "Informations Entreprise"


class Invoice(models.Model):
    """Invoice model with business rules and totals"""
    PAYMENT_METHOD_CHOICES = [
        ('ESPECES', 'Espèces'),
        ('CARTE_BANCAIRE', 'Carte bancaire'),
        ('VIREMENT', 'Virement'),
        ('CHEQUE', 'Chèque'),
        ('MOBILE_MONEY', 'Mobile Money'),
    ]

    STATUT_CHOICES = [
        ('BROUILLON', 'Brouillon'),
        ('VALIDEE', 'Validée'),
        ('ENVOYEE', 'Envoyée'),
        ('PARTIELLEMENT_PAYEE', 'Partiellement payée'),
        ('PAYEE', 'Payée'),
        ('EN_RETARD', 'En retard'),
        ('ANNULEE', 'Annulée'),
    ]

    invoice_number = models.CharField(max_length=20, unique=True, verbose_name="Numéro de facture")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices', verbose_name="Client")
    date = models.DateField(default=datetime.now, verbose_name="Date de facture")
    due_date = models.DateField(verbose_name="Date d'échéance")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='VIREMENT', verbose_name="Mode de règlement prévu")

    statut = models.CharField(max_length=30, choices=STATUT_CHOICES, default='BROUILLON', verbose_name="Statut")

    # Remises simplifiées
    remise_globale_pourcentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Remise globale %")
    remise_globale_montant = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Remise globale €")

    # Totaux
    sous_total_ht = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Sous-total HT")
    total_remise = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total remise")
    total_ht = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total HT")
    total_tva = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total TVA")
    total_ttc = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total TTC")

    # Payment tracking
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Montant payé")

    # Mentions métier
    notes = models.TextField(blank=True, null=True, verbose_name="Notes facture")
    payment_terms = models.CharField(max_length=255, blank=True, null=True, verbose_name="Conditions de paiement")
    legal_mentions = models.TextField(blank=True, null=True, verbose_name="Mentions légales")

    # Stock handling
    stock_movement_done = models.BooleanField(default=False, verbose_name="Mouvement de stock effectué")

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
    def clean(self):
        from django.core.exceptions import ValidationError
        # due date must be >= date
        if self.due_date and self.date and self.due_date < self.date:
            raise ValidationError({'due_date': 'La date d\'échéance doit être supérieure ou égale à la date de facture.'})
        # remises exclusive
        if self.remise_globale_pourcentage and self.remise_globale_montant and float(self.remise_globale_pourcentage) > 0 and float(self.remise_globale_montant) > 0:
            raise ValidationError('La remise globale en % et en montant ne peuvent pas être utilisées en même temps.')

    def calculate_totals(self):
        """Recalculate all totals from items and discounts.

        Ordre de calcul (respecte les standards de facturation FR) :
          1. Sous-total HT lignes (remises lignes déjà appliquées dans item.total_ht)
          2. TVA brute lignes
          3. Remise globale (% ou montant €) sur le sous-total HT
          4. Total HT = sous-total - remise globale
          5. TVA ajustée proportionnellement au ratio post-remise
             (préserve les taux multiples 5,5 / 10 / 20 % correctement)
          6. Total TTC = Total HT + TVA ajustée
        """
        from decimal import Decimal, ROUND_HALF_UP
        # On first save the invoice has no PK yet, so reverse relation access would fail.
        items = list(self.items.all()) if self.pk else []
        sous_total = Decimal('0.00')
        tva_brute = Decimal('0.00')
        for it in items:
            sous_total += (it.total_ht or Decimal('0.00'))
            tva_brute += (it.total_tva or Decimal('0.00'))

        # Apply global discount (percentage XOR amount)
        total_remise = Decimal('0.00')
        if self.remise_globale_pourcentage and float(self.remise_globale_pourcentage) > 0:
            total_remise = (sous_total * (Decimal(str(self.remise_globale_pourcentage)) / Decimal('100'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        elif self.remise_globale_montant and float(self.remise_globale_montant) > 0:
            total_remise = Decimal(str(self.remise_globale_montant)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Business safety: discount cannot exceed subtotal.
        if total_remise > sous_total:
            total_remise = sous_total

        total_ht = (sous_total - total_remise).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Recompute VAT proportionally so a global discount actually reduces TTC.
        if sous_total > 0 and total_remise > 0:
            ratio = (total_ht / sous_total)
            total_tva = (tva_brute * ratio).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            total_tva = tva_brute.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        total_ttc = (total_ht + total_tva).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Update fields
        self.sous_total_ht = sous_total
        self.total_remise = total_remise
        self.total_ht = total_ht
        self.total_tva = total_tva
        self.total_ttc = total_ttc

    @property
    def reste_a_payer(self):
        from decimal import Decimal
        return max(Decimal('0.00'), (self.total_ttc or 0) - (self.amount_paid or 0))

    @property
    def montant_paye(self):
        return self.amount_paid

    def _apply_stock_movement_if_needed(self):
        """Decrease product stock only when invoice becomes VALIDEE."""
        if self.statut != 'VALIDEE' or self.stock_movement_done:
            return

        for item in self.items.select_related('produit_service').all():
            if not item.produit_service:
                continue
            if not item.produit_service.can_allocate(item.quantite):
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    f"Stock insuffisant. Disponible : {item.produit_service.stock} unités."
                )
            item.produit_service.decrease_stock(item.quantite)

        self.stock_movement_done = True

    def update_statut_from_payment(self):
        """Set statut automatically from payments"""
        if self.statut == 'ANNULEE':
            return

        if float(self.amount_paid or 0) >= float(self.total_ttc or 0) and float(self.total_ttc or 0) > 0:
            self.statut = 'PAYEE'
        elif float(self.amount_paid or 0) > 0:
            self.statut = 'PARTIELLEMENT_PAYEE'
        else:
            if self.due_date and self.due_date < datetime.now().date() and float(self.reste_a_payer or 0) > 0:
                self.statut = 'EN_RETARD'
            else:
                if self.statut == 'BROUILLON':
                    self.statut = 'BROUILLON'
                else:
                    self.statut = 'VALIDEE'

    def save(self, *args, **kwargs):
        from django.core.exceptions import ValidationError

        previous_statut = None
        if self.pk:
            previous_statut = Invoice.objects.filter(pk=self.pk).values_list('statut', flat=True).first()

        # Ensure totals recalculated before saving
        self.calculate_totals()
        self.clean()
        # update payment-based statut
        self.update_statut_from_payment()

        # Apply stock movement only on transition to VALIDEE.
        if previous_statut != 'VALIDEE' and self.statut == 'VALIDEE':
            # Must already be saved to access reverse relation reliably.
            if not self.pk:
                super().save(*args, **kwargs)
            self._apply_stock_movement_if_needed()

        # Do not allow reverting payment amount below zero.
        if float(self.amount_paid or 0) < 0:
            raise ValidationError({'amount_paid': 'Le montant payé ne peut pas être négatif.'})

        super().save(*args, **kwargs)


class InvoiceItem(models.Model):
    """Invoice line item (LigneFacture) with automatic calculations

    Fields:
    - facture
    - produit/service
    - description
    - quantite
    - prix_unitaire_ht
    - taux_tva
    - unite
    - remise_pourcentage
    - total_ht, total_tva, total_ttc
    """
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items', verbose_name="Facture")
    produit_service = models.ForeignKey(Product, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Produit / Service")
    description = models.CharField(max_length=255, verbose_name="Description")
    quantite = models.DecimalField(max_digits=10, decimal_places=2, default=1, validators=[MinValueValidator(0.01)], verbose_name="Quantité")
    prix_unitaire_ht = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], default=0, verbose_name="Prix unitaire HT")
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2, default=20.00, verbose_name="Taux TVA")
    unite = models.CharField(max_length=10, blank=True, null=True, verbose_name="Unité")
    remise_pourcentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Remise %")

    # Totaux par ligne
    total_ht = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total HT")
    total_tva = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total TVA")
    total_ttc = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total TTC")

    class Meta:
        verbose_name = "Ligne de facture"
        verbose_name_plural = "Lignes de facture"

    def __str__(self):
        return f"{self.description} x{self.quantite}"

    # Compatibilité avec le code existant qui utilise encore item.product.
    @property
    def product(self):
        return self.produit_service

    @product.setter
    def product(self, value):
        self.produit_service = value

    @property
    def total(self):
        """Backward-compatible total (TTC)"""
        return self.total_ttc

    def clean(self):
        from django.core.exceptions import ValidationError
        # Quantite > 0
        if float(self.quantite or 0) <= 0:
            raise ValidationError({'quantite': 'La quantité doit être supérieure à 0.'})
        if float(self.prix_unitaire_ht or 0) < 0:
            raise ValidationError({'prix_unitaire_ht': 'Le prix unitaire doit être >= 0.'})
        if float(self.taux_tva or 0) < 0 or float(self.taux_tva or 0) > 100:
            raise ValidationError({'taux_tva': 'La TVA doit être comprise entre 0 et 100.'})
        if float(self.remise_pourcentage or 0) < 0 or float(self.remise_pourcentage or 0) > 100:
            raise ValidationError({'remise_pourcentage': 'La remise doit être entre 0 et 100.'})

    def save(self, *args, **kwargs):
        """Auto-fill fields from selected product and compute totals."""
        from decimal import Decimal, ROUND_HALF_UP
        if self.produit_service:
            # auto-fill description, prix_unitaire_ht, taux_tva, unite if not provided
            if not self.description:
                self.description = self.produit_service.description or self.produit_service.name
            if (not self.prix_unitaire_ht or float(self.prix_unitaire_ht) == 0) and getattr(self.produit_service, 'prix_unitaire_ht', None) is not None:
                self.prix_unitaire_ht = self.produit_service.prix_unitaire_ht
            if (not self.taux_tva or float(self.taux_tva) == 0) and getattr(self.produit_service, 'taux_tva', None) is not None:
                self.taux_tva = self.produit_service.taux_tva
            if not self.unite and getattr(self.produit_service, 'unite', None) is not None:
                self.unite = self.produit_service.unite

        # compute totals
        q = Decimal(str(self.quantite or 0))
        pu = Decimal(str(self.prix_unitaire_ht or 0))
        remise = Decimal(str(self.remise_pourcentage or 0))

        line_ht = (q * pu).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        remise_amount = (line_ht * (remise / Decimal('100'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_ht = (line_ht - remise_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_tva = (total_ht * (Decimal(str(self.taux_tva or 0)) / Decimal('100'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_ttc = (total_ht + total_tva).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        self.total_ht = total_ht
        self.total_tva = total_tva
        self.total_ttc = total_ttc

        super().save(*args, **kwargs)


class Payment(models.Model):
    """Payment record"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments', verbose_name="Facture")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Montant")
    payment_method = models.CharField(max_length=20, choices=Invoice.PAYMENT_METHOD_CHOICES, blank=True, verbose_name="Méthode de paiement utilisée")
    payment_date = models.DateField(default=datetime.now, verbose_name="Date de paiement")
    reference = models.CharField(max_length=100, blank=True, null=True, verbose_name="Référence")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    email_sent = models.BooleanField(default=False, verbose_name="Email envoyé")
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
    """Business notification with compatibility aliases for legacy fields."""
    TYPE_NOTIFICATION_CHOICES = [
        ('FACTURE', 'Facture'),
        ('PAIEMENT', 'Paiement'),
        ('STOCK', 'Stock'),
        ('CLIENT', 'Client'),
        ('SYSTEME', 'Système'),
    ]

    NIVEAU_CHOICES = [
        ('HAUTE', 'Haute'),
        ('MOYENNE', 'Moyenne'),
        ('BASSE', 'Basse'),
    ]

    # Required business fields
    titre = models.CharField(max_length=255, verbose_name="Titre")
    message = models.TextField(verbose_name="Message")
    type_notification = models.CharField(
        max_length=20,
        choices=TYPE_NOTIFICATION_CHOICES,
        default='SYSTEME',
        verbose_name="Type de notification"
    )
    niveau = models.CharField(max_length=20, choices=NIVEAU_CHOICES, default='BASSE', verbose_name="Niveau")
    lu = models.BooleanField(default=False, verbose_name="Lu")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    lien = models.CharField(max_length=255, blank=True, null=True, verbose_name="Lien")

    # Optional relations
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='notifications', verbose_name="Client", blank=True, null=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, blank=True, null=True, related_name='notifications', verbose_name="Facture")
    quote = models.ForeignKey(Quote, on_delete=models.SET_NULL, blank=True, null=True, related_name='notifications', verbose_name="Devis")

    # Legacy fields kept for backward compatibility
    type = models.CharField(max_length=50, blank=True, null=True, verbose_name="Type legacy")
    status = models.CharField(max_length=20, default='pending', verbose_name="Statut legacy")
    subject = models.CharField(max_length=255, blank=True, null=True, verbose_name="Sujet legacy")
    recipient_email = models.EmailField(blank=True, null=True, verbose_name="Email du destinataire")
    created_at = models.DateTimeField(blank=True, null=True)
    sent_at = models.DateTimeField(blank=True, null=True, verbose_name="Date d'envoi")
    error_message = models.TextField(blank=True, null=True, verbose_name="Message d'erreur")

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['-date_creation']),
            models.Index(fields=['type_notification', 'niveau']),
            models.Index(fields=['lu']),
        ]

    def __str__(self):
        return f"{self.titre}"

    @property
    def bootstrap_badge_class(self):
        mapping = {
            'HAUTE': 'danger',
            'MOYENNE': 'warning text-dark',
            'BASSE': 'secondary',
        }
        return mapping.get(self.niveau, 'secondary')

    def save(self, *args, **kwargs):
        # Keep legacy fields synchronized to avoid breaking old code paths.
        if self.niveau in ['ERROR']:
            self.niveau = 'HAUTE'
        elif self.niveau in ['WARNING']:
            self.niveau = 'MOYENNE'
        elif self.niveau in ['INFO', 'SUCCESS', None, '']:
            self.niveau = 'BASSE'

        if not self.subject and self.titre:
            self.subject = self.titre
        if not self.titre and self.subject:
            self.titre = self.subject

        if not self.type and self.type_notification:
            self.type = self.type_notification
        if not self.type_notification and self.type:
            self.type_notification = self.type

        self.status = 'read' if self.lu else (self.status or 'pending')

        super().save(*args, **kwargs)

        # date_creation is the source of truth; keep created_at as compatibility mirror.
        if self.created_at is None:
            Notification.objects.filter(pk=self.pk, created_at__isnull=True).update(created_at=self.date_creation)


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
