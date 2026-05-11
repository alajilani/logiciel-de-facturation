from django.test import TestCase, Client as DjangoClient
from django.contrib.auth.models import User
from invoice_app.models import Client, Product, Invoice, InvoiceItem, Payment, CompanyInfo
from datetime import datetime, timedelta

class ClientModelTest(TestCase):
    def setUp(self):
        self.client_obj = Client.objects.create(
            name="Test Client",
            email="test@example.com",
            phone="0123456789",
            country="France"
        )
    
    def test_client_creation(self):
        self.assertEqual(self.client_obj.name, "Test Client")
        self.assertEqual(self.client_obj.country, "France")
    
    def test_client_str(self):
        self.assertEqual(str(self.client_obj), "Test Client")


class ProductModelTest(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Test Product",
            price=99.99,
            reference="TEST001"
        )
    
    def test_product_creation(self):
        self.assertEqual(self.product.name, "Test Product")
        self.assertEqual(self.product.price, 99.99)
    
    def test_unique_reference(self):
        with self.assertRaises(Exception):
            Product.objects.create(
                name="Another Product",
                price=50.00,
                reference="TEST001"
            )


class InvoiceModelTest(TestCase):
    def setUp(self):
        self.client = Client.objects.create(name="Test Client", country="France")
        self.invoice = Invoice.objects.create(
            invoice_number="2025-001",
            client=self.client,
            date=datetime.now().date(),
            due_date=datetime.now().date() + timedelta(days=30),
            total=100.00
        )
    
    def test_invoice_creation(self):
        self.assertEqual(self.invoice.invoice_number, "2025-001")
        self.assertEqual(self.invoice.total, 100.00)
    
    def test_remaining_amount(self):
        self.invoice.amount_paid = 30.00
        self.assertEqual(self.invoice.remaining_amount, 70.00)


class InvoiceViewsTest(TestCase):
    def setUp(self):
        self.client = DjangoClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.test_client = Client.objects.create(
            name="Test Client",
            country="France"
        )
    
    def test_dashboard_view(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoice_app/dashboard.html')
    
    def test_client_list_view(self):
        response = self.client.get('/clients/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoice_app/client_list.html')
