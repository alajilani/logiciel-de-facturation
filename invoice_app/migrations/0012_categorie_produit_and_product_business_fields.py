from django.db import migrations, models
import django.db.models.deletion


def migrate_product_categories(apps, schema_editor):
    Product = apps.get_model('invoice_app', 'Product')
    CategorieProduit = apps.get_model('invoice_app', 'CategorieProduit')

    for product in Product.objects.all():
        legacy = (getattr(product, 'categorie_legacy', None) or '').strip()
        if not legacy:
            continue

        category, _ = CategorieProduit.objects.get_or_create(
            nom=legacy,
            defaults={
                'description': '',
                'statut': 'ACTIF',
            }
        )
        product.categorie_id = category.id
        product.save(update_fields=['categorie'])


class Migration(migrations.Migration):

    dependencies = [
        ('invoice_app', '0011_alter_product_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CategorieProduit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=120, unique=True, verbose_name='Nom')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('statut', models.CharField(choices=[('ACTIF', 'Actif'), ('INACTIF', 'Inactif')], default='ACTIF', max_length=10, verbose_name='Statut')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Catégorie produit/service',
                'verbose_name_plural': 'Catégories produit/service',
                'ordering': ['nom'],
            },
        ),
        migrations.RenameField(
            model_name='product',
            old_name='categorie',
            new_name='categorie_legacy',
        ),
        migrations.AddField(
            model_name='product',
            name='categorie',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='produits', to='invoice_app.categorieproduit', verbose_name='Catégorie'),
        ),
        migrations.RunPython(migrate_product_categories, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='product',
            name='categorie_legacy',
        ),
        migrations.AddField(
            model_name='product',
            name='derniere_modification_prix',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Dernière modification du prix'),
        ),
        migrations.AddField(
            model_name='product',
            name='disponible_vente',
            field=models.BooleanField(default=True, verbose_name='Disponible à la vente'),
        ),
        migrations.AddField(
            model_name='product',
            name='prix_unitaire_ttc',
            field=models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=12, verbose_name='Prix unitaire TTC'),
        ),
        migrations.RenameField(
            model_name='invoiceitem',
            old_name='product',
            new_name='produit_service',
        ),
    ]
