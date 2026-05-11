from rest_framework import serializers
from .models import Client, Product, Invoice, InvoiceItem, Payment, CompanyInfo


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'name', 'email', 'phone', 'delivery_address', 'billing_address', 'country', 'tva_intra']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'reference', 'description']


class InvoiceItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = InvoiceItem
        fields = ['id', 'description', 'quantity', 'price', 'product', 'product_name', 'total']
        read_only_fields = ['total']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'invoice', 'amount', 'payment_method', 'payment_date', 'reference', 'notes']


class InvoiceSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    items = InvoiceItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'client', 'client_name', 'date', 'due_date',
            'payment_method', 'subtotal', 'remise_amount', 'rabais_amount',
            'escompte_amount', 'total_discount', 'tva_amount', 'total',
            'amount_paid', 'remaining_amount', 'payment_status', 'items', 'payments'
        ]
        read_only_fields = ['invoice_number', 'subtotal', 'total', 'remaining_amount']


class CompanyInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyInfo
        fields = ['id', 'name', 'address', 'phone', 'email', 'website', 'siret', 'siren', 'tva_number', 'country']
