#!/usr/bin/env python
"""
Script to populate the database with sample data for development
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'invoice_project.settings')
django.setup()

from invoice_app.models import Client, Product, CompanyInfo, Invoice, InvoiceItem, Payment
from datetime import datetime, timedelta

def populate_data():
    print("🚀 Populating database with sample data...")
    
    # Create Company Info
    company, created = CompanyInfo.objects.get_or_create(
        id=1,
        defaults={
            'name': 'Mon Entreprise',
            'address': '123 Rue de Paris, 75000 Paris',
            'phone': '01 23 45 67 89',
            'email': 'info@example.com',
            'website': 'https://www.example.com',
            'siret': '12345678901234',
            'siren': '123456789',
            'tva_number': 'FR12345678901',
            'country': 'France'
        }
    )
    print(f"✓ Company: {company.name}")
    
    # Create Clients
    clients_data = [
        {
            'name': 'Entreprise Alpha',
            'email': 'contact@alpha.fr',
            'phone': '01 11 11 11 11',
            'country': 'France',
            'delivery_address': '123 Rue A, 75001 Paris',
            'billing_address': '123 Rue A, 75001 Paris',
        },
        {
            'name': 'Société Beta',
            'email': 'info@beta.de',
            'phone': '+49 123 456789',
            'country': 'Germany',
            'delivery_address': 'Unter den Linden 1, 10117 Berlin',
            'billing_address': 'Unter den Linden 1, 10117 Berlin',
            'tva_intra': 'DE123456789',
        },
        {
            'name': 'Compagnie Gamma',
            'email': 'hello@gamma.uk',
            'phone': '+44 20 7946 0958',
            'country': 'United Kingdom',
            'delivery_address': '10 Downing Street, SW1A 2AA London',
            'billing_address': '10 Downing Street, SW1A 2AA London',
        },
    ]
    
    created_clients = []
    for client_data in clients_data:
        client, created = Client.objects.get_or_create(**client_data)
        if created:
            print(f"✓ Client: {client.name}")
        created_clients.append(client)
    
    # Create Products
    products_data = [
        {'name': 'Développement Web', 'price': 150.00, 'reference': 'DEV-001', 'description': 'Heure de développement web'},
        {'name': 'Design Graphique', 'price': 100.00, 'reference': 'DESIGN-001', 'description': 'Heure de design'},
        {'name': 'Consultation', 'price': 75.00, 'reference': 'CONS-001', 'description': 'Heure de consultation'},
        {'name': 'Support Technique', 'price': 60.00, 'reference': 'SUPP-001', 'description': 'Heure de support'},
        {'name': 'Licence Logiciel', 'price': 500.00, 'reference': 'LIC-001', 'description': 'Licence annuelle'},
    ]
    
    created_products = []
    for product_data in products_data:
        product, created = Product.objects.get_or_create(**product_data)
        if created:
            print(f"✓ Product: {product.name}")
        created_products.append(product)
    
    # Create Invoices with Items
    base_date = datetime.now().date()
    for i, client in enumerate(created_clients):
        for j in range(3):
            invoice_date = base_date - timedelta(days=30 * j)
            invoice_number = f"2025-{i*3 + j + 1:03d}"
            
            invoice, created = Invoice.objects.get_or_create(
                invoice_number=invoice_number,
                defaults={
                    'client': client,
                    'date': invoice_date,
                    'due_date': invoice_date + timedelta(days=30),
                    'payment_method': 'bank_transfer',
                }
            )
            
            if created:
                # Add items
                for idx in range(2, 4):
                    product = created_products[idx % len(created_products)]
                    item = InvoiceItem.objects.create(
                        invoice=invoice,
                        description=product.name,
                        quantity=2 + j,
                        price=product.price,
                        product=product
                    )
                
                # Calculate totals
                subtotal = sum(item.quantity * item.price for item in invoice.items.all())
                invoice.subtotal = subtotal
                invoice.remise_amount = subtotal * 0.05 if j == 0 else 0
                invoice.tva_amount = (subtotal - invoice.remise_amount) * 0.20
                invoice.total = subtotal - invoice.remise_amount + invoice.tva_amount
                
                # Add payment if overdue
                if j > 0:
                    invoice.amount_paid = invoice.total
                    invoice.payment_status = 'paid'
                    Payment.objects.create(
                        invoice=invoice,
                        amount=invoice.total,
                        payment_method='bank_transfer',
                        payment_date=invoice_date + timedelta(days=5),
                        reference=f"VIR-2025-{i*3 + j + 1:03d}"
                    )
                
                invoice.save()
                print(f"✓ Invoice: {invoice_number} ({client.name})")
    
    print("\n✅ Database population completed!")
    print(f"Total clients: {Client.objects.count()}")
    print(f"Total products: {Product.objects.count()}")
    print(f"Total invoices: {Invoice.objects.count()}")

if __name__ == '__main__':
    populate_data()
