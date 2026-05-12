# Generated migration for Tier 2 features
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
from datetime import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('invoice_app', '0004_auditlog_auditlog_invoice_app_model_650d25_idx_and_more'),
    ]

    operations = [
        # Add currency fields to Invoice
        migrations.AddField(
            model_name='invoice',
            name='currency',
            field=models.CharField(choices=[('EUR', 'Euro'), ('USD', 'Dollar US'), ('GBP', 'Livre Sterling')], default='EUR', max_length=3, verbose_name='Devise'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='exchange_rate',
            field=models.DecimalField(decimal_places=4, default=1.0, max_digits=8, verbose_name='Taux de change'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='original_currency',
            field=models.CharField(default='EUR', max_length=3, verbose_name='Devise originale'),
        ),
        # Add archive fields to Invoice
        migrations.AddField(
            model_name='invoice',
            name='is_archived',
            field=models.BooleanField(default=False, verbose_name='Archivee'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='archived_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name="Date d'archivage"),
        ),
        migrations.AddField(
            model_name='invoice',
            name='archived_by',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Archivee par'),
        ),
        
        # Add currency fields to Quote
        migrations.AddField(
            model_name='quote',
            name='currency',
            field=models.CharField(choices=[('EUR', 'Euro'), ('USD', 'Dollar US'), ('GBP', 'Livre Sterling')], default='EUR', max_length=3, verbose_name='Devise'),
        ),
        migrations.AddField(
            model_name='quote',
            name='exchange_rate',
            field=models.DecimalField(decimal_places=4, default=1.0, max_digits=8, verbose_name='Taux de change'),
        ),
        migrations.AddField(
            model_name='quote',
            name='original_currency',
            field=models.CharField(default='EUR', max_length=3, verbose_name='Devise originale'),
        ),
        
        # Add currency to Payment
        migrations.AddField(
            model_name='payment',
            name='currency',
            field=models.CharField(choices=[('EUR', 'Euro'), ('USD', 'Dollar US'), ('GBP', 'Livre Sterling')], default='EUR', max_length=3, verbose_name='Devise'),
        ),
        
        # Create ExchangeRate model
        migrations.CreateModel(
            name='ExchangeRate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_currency', models.CharField(choices=[('EUR', 'Euro'), ('USD', 'Dollar US'), ('GBP', 'Livre Sterling')], max_length=3, verbose_name='Devise source')),
                ('to_currency', models.CharField(choices=[('EUR', 'Euro'), ('USD', 'Dollar US'), ('GBP', 'Livre Sterling')], max_length=3, verbose_name='Devise cible')),
                ('rate', models.DecimalField(decimal_places=4, max_digits=8, verbose_name='Taux de change')),
                ('date', models.DateField(default=datetime.now, verbose_name='Date du taux')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Taux de change',
                'verbose_name_plural': 'Taux de change',
                'ordering': ['-date'],
            },
        ),
        
        # Create SearchIndex model
        migrations.CreateModel(
            name='SearchIndex',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content_type', models.CharField(choices=[('invoice', 'Facture'), ('client', 'Client'), ('quote', 'Devis')], max_length=20, verbose_name='Type de contenu')),
                ('object_id', models.IntegerField(verbose_name="ID de l'objet")),
                ('search_text', models.TextField(verbose_name='Texte de recherche')),
                ('keywords', models.TextField(verbose_name='Mots-cles')),
                ('document_number', models.CharField(blank=True, max_length=20, null=True, verbose_name='Numero du document')),
                ('client_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Nom du client')),
                ('amount', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Montant')),
                ('date', models.DateField(blank=True, null=True, verbose_name='Date')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Index de recherche',
                'verbose_name_plural': 'Index de recherche',
            },
        ),
        
        # Create ArchiveLog model
        migrations.CreateModel(
            name='ArchiveLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('archived_by', models.CharField(blank=True, max_length=255, null=True, verbose_name='Archivee par')),
                ('archived_at', models.DateTimeField(auto_now_add=True, verbose_name="Date d'archivage")),
                ('reason', models.TextField(blank=True, null=True, verbose_name="Raison de l'archivage")),
                ('unarchived_by', models.CharField(blank=True, max_length=255, null=True, verbose_name='Restauree par')),
                ('unarchived_at', models.DateTimeField(blank=True, null=True, verbose_name='Date de restauration')),
                ('unarchive_reason', models.TextField(blank=True, null=True, verbose_name='Raison de la restauration')),
                ('invoice', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='archive_log', to='invoice_app.invoice', verbose_name='Facture')),
            ],
            options={
                'verbose_name': "Journal d'archivage",
                'verbose_name_plural': "Journaux d'archivage",
                'ordering': ['-archived_at'],
            },
        ),
        
        # Add indexes to SearchIndex
        migrations.AddIndex(
            model_name='searchindex',
            index=models.Index(fields=['content_type', 'object_id'], name='invoice_ap_content_d8f5c6_idx'),
        ),
        migrations.AddIndex(
            model_name='searchindex',
            index=models.Index(fields=['search_text'], name='invoice_ap_search__f4a2b8_idx'),
        ),
        migrations.AddIndex(
            model_name='searchindex',
            index=models.Index(fields=['keywords'], name='invoice_ap_keyword_3c9d1e_idx'),
        ),
        migrations.AddIndex(
            model_name='searchindex',
            index=models.Index(fields=['document_number'], name='invoice_ap_documen_7b5e2a_idx'),
        ),
        migrations.AddIndex(
            model_name='searchindex',
            index=models.Index(fields=['client_name'], name='invoice_ap_client__6f3c9a_idx'),
        ),
        
        # Add index to ExchangeRate
        migrations.AddIndex(
            model_name='exchangerate',
            index=models.Index(fields=['from_currency', 'to_currency', '-date'], name='invoice_ap_from_cu_9d2e4f_idx'),
        ),
        
        # Add unique constraint to ExchangeRate
        migrations.AlterUniqueTogether(
            name='exchangerate',
            unique_together={('from_currency', 'to_currency', 'date')},
        ),
    ]
