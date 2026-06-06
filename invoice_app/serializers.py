from rest_framework import serializers
from .models import Client, Product, Invoice, InvoiceItem, Payment, CompanyInfo, CategorieProduit


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'nom', 'email', 'telephone', 'adresse_facturation', 'pays_facturation', 'numero_tva_intracommunautaire']


class ProductSerializer(serializers.ModelSerializer):
    categorie_nom = serializers.CharField(source='categorie.nom', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'reference', 'type_item', 'categorie', 'categorie_nom',
            'description', 'prix_unitaire_ht', 'prix_unitaire_ttc', 'taux_tva', 'unite',
            'suivre_stock', 'stock', 'seuil_alerte', 'disponible_vente',
            'derniere_modification_prix', 'statut'
        ]


class InvoiceItemSerializer(serializers.ModelSerializer):
    produit_service_name = serializers.CharField(source='produit_service.name', read_only=True)

    class Meta:
        model = InvoiceItem
        fields = ['id', 'description', 'quantite', 'prix_unitaire_ht', 'taux_tva', 'unite',
                  'remise_pourcentage', 'total_ht', 'total_tva', 'total_ttc', 'produit_service', 'produit_service_name']
        read_only_fields = ['total_ht', 'total_tva', 'total_ttc']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'invoice', 'amount', 'payment_method', 'payment_date', 'reference', 'notes']


class InvoiceSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.nom', read_only=True)
    items = InvoiceItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    reste_a_payer = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'client', 'client_name', 'date', 'due_date',
            'payment_method', 'statut',
            'remise_globale_pourcentage', 'remise_globale_montant',
            'sous_total_ht', 'total_remise', 'total_ht', 'total_tva', 'total_ttc',
            'amount_paid', 'reste_a_payer', 'items', 'payments'
        ]
        read_only_fields = ['invoice_number', 'sous_total_ht', 'total_remise', 'total_ht', 'total_tva', 'total_ttc', 'reste_a_payer']


class CompanyInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyInfo
        fields = ['id', 'name', 'address', 'phone', 'email', 'website', 'siret', 'siren', 'tva_number', 'country']
